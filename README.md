# MaSGA - Make Sauna Great Again [Back-end]
Winner of the Junction 2018 challenge "Hack the Sauna" by Vaisala

This is the back-end of the project, the code of the front-end can be found in [Addono/masga](https://github.com/Addono/masga) repository.

A live version of the front-end can be found [here](https://aknapen.nl/masga). The back-end is accessible at:
[https://us-central1-junction-2018.cloudfunctions.net/get-percentage](https://us-central1-junction-2018.cloudfunctions.net/get-percentage).

## Deployment
The back-end is written in Python and made to run on the serverless (Function-as-a-Service) public cloud environment Google Functions. To deploy the code upload the content of this repository as a new Google Cloud Function. It requires both the `main.py` and `requirements.txt` to be present. If the data should be retrieved from a different API, then alter the `BASE_URL` variable in `main.py`.
