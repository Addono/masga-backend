import requests
import json
import math

BASE_URL = "https://apigtw.vaisala.com/hackjunction2018/saunameasurements/"


def get_latest_url_for_device_id(device_id):
    return BASE_URL + "latest?SensorID=" + device_id + "&limit=1"


def poll_data(device_id):
    url = get_latest_url_for_device_id(device_id)
    response = requests.get(url)
    object = json.loads(response.content)

    return object


def extract_value(data, key):
    assert len(data) == 1

    return data[0]['Measurements'][key]['value']


def poll_api():
    # Bench2: Temp, Bench2: Hum / 10, Floor1: Temp, Bench1: CO2 / 100
    print("--------")

    values = [
        ["Bench1", "Temperature", 1],
        ["Bench1", "Carbon Dioxide concentration", 10],
        ["Floor1", "Temperature", 1],
        ["Bench2", "Relative humidity", 100],
    ]

    all_sensors = set([row[0] for row in values])
    all_data = {device_id: poll_data(device_id) for device_id in all_sensors}

    input = []
    normalization = []
    for (device_id, value, n) in values:
        output = extract_value(all_data[device_id], value)
        input.append(output)
        normalization.append(n)
        print(device_id + "\t" + value + ":\t" + str(output))

    optimal = [67.77, 1049, 74.75, 27.37]

    try:
        return quadro(input, optimal, normalization)
    except ValueError as e:
        print("Math error: %s" % e)

    return 0


def quadro(c: list, d: list, n: list):
    """
    :param c: The input values to apply the fuzzy logic on.
    :param d: The optimal values for the input values.
    :return: Relation percentage.
    """
    assert len(c) == len(d) == len(n) == 4

    c = [c[i] / n[i] for i in range(4)]
    d = [d[i] / n[i] for i in range(4)]

    wa = 1
    wb = 1

    # a(1) = (c(1) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # a(2) = (c(2) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # a(3) = (c(3) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # a(4) = (c(4) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # b(1) = (d(1) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # b(2) = (d(2) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # b(3) = (d(3) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    # b(4) = (d(4) - min(c(1), d(1))) / (max(c(4), d(4)) - min(c(1), d(1)));
    min_low = min(c[0], d[0])
    max_high = max(c[3], d[3])
    a = [(c[i] - min_low) / (max_high - min_low) for i in range(4)]
    b = [(d[i] - min_low) / (max_high - min_low) for i in range(4)]

    # s50 = 1 - (abs(c(1) - d(1)) + abs(c(2) - d(2)) + abs(c(3) - d(3)) + abs(c(4) - d(4))) / 3;
    # s2 = 1 - (abs(a(1) - b(1)) + abs(a(2) - b(2)) + abs(a(3) - b(3)) + abs(a(4) - b(4))) / 4;
    sumAbsDiff = sum([abs(a[i] - b[i]) for i in range(4)])
    s2 = 1 - sumAbsDiff / 4

    # if a(1)~=a(4)
    #   ysa = (wa * ((a(3) - a(2)) / (a(4) - a(1)) + 2)) / 6;
    if a[0] != a[3]:
        ysa = (wa * ((a[2] - a[1]) / (a[3] - a[0]) + 2)) / 6

    # if a(1) == a(4)
    #     ysa = wa / 2;
    else:
        ysa = wa / 2

    # if wa == 0
    #     xsa = (a(4) + a(1)) / 2;
    # else
    #     xsa = (ysa * (a(3) + a(2)) + (a(4) + a(1)) * (wa - ysa)) / (2 * wa);
    if wa == 0:
        xsa = (a[3] + a[0]) / 2
    else:
        xsa = (ysa * (a[2] + a[1]) + (a[3] + a[0]) * (wa - ysa)) / (2 * wa)

    # if b(1)~=b(4)
    #     ysb = (wb * ((b(3) - b(2)) / (b(4) - b(1)) + 2)) / 6;
    # end
    # if b(1) == b(4)
    #     ysb = wb / 2;
    # end
    if b[0] != b[3]:
        ysb = (wb * ((b[2] - b[1]) / (b[3] - b[0]) + 2)) / 6
    else:
        ysb = wb / 2

    # if wb == 0
    #     xsb = (b(4) + b(1)) / 2;
    # else
    #     xsb = (ysb * (b(3) + b(2)) + (b(4) + b(1)) * (wb - ysb)) / (2 * wb);
    # end
    if wb == 0:
        xsb = (b[3] + b[0]) / 2
    else:
        xsb = (ysb * (b[2] + b[1]) + (b[3] + b[0]) * (wb - ysb)) / (2 * wb)

    # sa = a(4) - a(1);
    sa = a[3] - a[0]

    # sb = b(4) - b(1);
    sb = b[3] - b[0]

    # if sa + sb > 0
    #     BSS = 1;
    # end
    if sa + sb > 0:
        BSS = 1
    # if sa + sb == 0
    #     BSS = 0;
    elif sa + sb == 0:
        BSS = 0

    # s3 = ((1 - abs(xsa - xsb)) ^ BSS) * (min(ysa, ysb)) / (max(ysa, ysb));
    s3 = math.pow((1 - abs(xsa - xsb)), BSS) * min(ysa, ysb) / max(ysa, ysb)

    # if a(4) - a(1)~=0
    #    pa = sqrt((a(1) - a(2)) ^ 2 + wa ^ 2) + sqrt((a(3) - a(4)) ^ 2 + wa ^ 2) + a(3) - a(2) + a(4) - a(1);
    if a[3] != a[0]:
        pa = math.sqrt(math.pow(a[0] - a[1], 2) + wa * wa) + math.sqrt(math.pow(a[2] - a[3], 2) + wa * wa) + a[2] - a[1] + a[3] - a[0]

    # if a(4) - a(1) == 0
    #     pa = wa;
    if a[3] == a[0]:
        pa = wa

    # if b(4) - b(1)~=0
    # pb = sqrt((b(1) - b(2)) ^ 2 + wb ^ 2) + sqrt((b(3) - b(4)) ^ 2 + wb ^ 2) + b(3) - b(2) + b(4) - b(1);
    if b[3] != b[0]:
        pb = math.sqrt(math.pow(b[0] - b[1], 2) + wb * wb) + math.sqrt(math.pow(b[2] - b[3], 2) + wb * wb) + b[2] - b[1] + b[3] - b[0]

    # if b(4) - b(1) == 0
    #     pb = wb;
    if b[3] == b[0]:
        pb = wb

    # aa = 0.5 * wa * (a(2) - a(1) + a(4) - a(3)) + (a(3) - a(2)) * wa;
    # ab = 0.5 * wb * (b(2) - b(1) + b(4) - b(3)) + (b(3) - b(2)) * wb;
    aa = 0.5 * wa * (a[1] - a[0] + a[3] - a[2]) + (a[2] - a[1]) * wa
    ab = 0.5 * wb * (b[1] - b[0] + b[3] - b[2]) + (b[2] - b[1]) * wb

    # s4 = (min(pa, pb) + min(aa, ab)) / (max(pa, pb) + max(aa, ab));
    s4 = (min(pa, pb) + min(aa, ab)) / (max(pa, pb) + max(aa, ab))

    # v = 1 - abs(xsa - xsb);
    v = 1 - abs(xsa - xsb)

    # S21 = ((s2) ^ v) * s4;
    # S21 = math.pow(s2, v) * s4 # REDUNDANT, never used until overwritten.

    # z = (abs(a(1) - b(1)) + abs(a(2) - b(2)) + abs(a(3) - b(3)) + abs(a(4) - b(4))) / 4;
    z = (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) + abs(a[3] - b[3])) / 4

    # t = abs(xsa - xsb);
    t = abs(xsa - xsb)

    # tz = -abs(z * t);
    tz = -abs(z * t)

    # if c(1) == c(2) == c(3) == c(4), d(1) == d(2) == d(3) == d(4);
    # S21 = (exp(1) ^ tz) * s4;
    # else
    # S21 = ((s2) ^ v) * s4;
    # end
    if c[0] == c[1] == c[2] == c[3] and d[0] == d[1] == d[2] == d[3]:
        S21 = (math.pow(math.exp(1), tz)) * s4
    else:
        S21 = math.pow(s2, v) * s4

    # S22 = ((s2) ^ v);
    # S22 = math.pow(s2, v)

    return S21


def access_point(request):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    return json.dumps({"percentage": poll_api()}), 200, headers
