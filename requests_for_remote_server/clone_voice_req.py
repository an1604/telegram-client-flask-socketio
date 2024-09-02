import os
import time
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('SERVER_URL')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def send_speech_generation_request(text, profile_name, cps, regenerate):
    logging.info(
        f"send_speech_generation_request: Sending request to server with text: {text}, profile_name: {profile_name}, cps: {cps}, regenerate: {regenerate}")
    payload = {
        'text': text,
        'profile_name': profile_name,
        'cps': cps
    }
    url = f'{URL}/generate_speech' if not regenerate else f'{URL}/regenerate_audio'
    try:
        response = requests.post(url, json=payload)

        # Check if the response status code indicates success
        if response.status_code == 202:
            try:
                response_json = response.json()
                logging.info(f"send_speech_generation_request: Server accepted the task: {response_json}")
                return response_json.get('task_id')
            except ValueError as e:
                logging.error(f"send_speech_generation_request: Failed to parse JSON response: {e}. Response text: {response.text}")
                return None
        else:
            logging.error(
                f"send_speech_generation_request: Error from server: {response.status_code}, Response text: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"send_speech_generation_request: An error occurred while sending request: {e}")
        return None


def wait_for_result(task_id, profile_name, output_filename):
    logging.info(f"wait_for_result: Waiting for result for task_id: {task_id}, profile_name: {profile_name}")
    if task_id:
        requests_counter = 0
        get_audio_after_gen_req = f'{URL}/get_result/{task_id}'
        file_ready = False

        while not file_ready:
            if requests_counter > 13:
                logging.warning("wait_for_result: Exceeded maximum request attempts, exiting loop.")
                break
            requests_counter += 1

            time.sleep(3)

            try:
                response = requests.get(get_audio_after_gen_req.format(task_id=task_id))
                if response.status_code == 200:
                    if response.headers["content-type"].strip().startswith("application/json"):
                        res = response.json()
                        logging.info(f"wait_for_result: Response from server received: {res}")
                        if 'status' in res and res['status'] == 'pending':
                            time.sleep(3)
                    else:
                        file_ready = True
                        with open(output_filename, 'wb') as f:
                            f.write(response.content)
                        logging.info(f"wait_for_result: Audio file saved to {output_filename}")
                        return True
                else:
                    logging.error(
                        f"wait_for_result: Failed to get result from server, status code: {response.status_code}")
            except Exception as e:
                logging.error(f"wait_for_result: An error occurred while waiting for result: {e}")
        logging.error("wait_for_result: Failed to send the task to the server.")
        return False
