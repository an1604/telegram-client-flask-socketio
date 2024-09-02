import os
import string
import logging
from requests_for_remote_server.clone_voice_req import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def clean_text(text):
    logging.info(f"clean_text: Cleaning text: {text}")
    try:
        text = text.replace(" ", "_")
        text = text.translate(str.maketrans('', '', string.punctuation))
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        text = ''.join(c for c in text if c in valid_chars)
        return text.lower()
    except Exception as e:
        logging.error(f"clean_text: Error cleaning text {text}: {e}")


def get_output_filename(profile_name, tts):
    logging.info(f"get_output_filename: Generating output filename for profile {profile_name} and tts {tts}")
    try:
        profile_dir = os.path.join(os.getcwd(), profile_name)
        os.makedirs(profile_dir, exist_ok=True)
        output_filename = os.path.join(profile_dir, f"{clean_text(tts)}.wav")
        return output_filename
    except Exception as e:
        logging.error(
            f"get_output_filename: Error generating output filename for profile {profile_name} and tts {tts}: {e}")


def clone(text, profile_name_for_tts, output_filename, cps, regenerate=False):
    logging.info(
        f"clone: Cloning voice with text: {text}, profile: {profile_name_for_tts}, cps: {cps}, regenerate: {regenerate}")
    try:
        task_id = send_speech_generation_request(text=text, profile_name=profile_name_for_tts, cps=cps,
                                                 regenerate=regenerate)
        if wait_for_result(task_id=task_id, output_filename=output_filename, profile_name=profile_name_for_tts):
            logging.info(f"clone: Speech generation succeeded, output saved to {output_filename}")
            return output_filename
        logging.warning(f"clone: Speech generation failed for text: {text} with profile: {profile_name_for_tts}")
        return None
    except Exception as e:
        logging.error(f"clone: Error in cloning voice with text {text}, profile {profile_name_for_tts}: {e}")
