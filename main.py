from time import sleep
from requests import get
from subprocess import run

file = open(".token", "r")
SLEEP_TIME_SECS = 1
PRIVATE_TOKEN = file.readline()
BASE_API_PATH = 'https://gitlab.hpi.de/api/v4/projects/8839/pipelines?ref=main&order_by=updated_at&sort=desc'

prev_traffic_light_status = 'none'
traffic_light_status = 'none'

latest_job = get(
        f'{BASE_API_PATH}&scope=finished',
        headers={'PRIVATE-TOKEN': PRIVATE_TOKEN},
    ).json()[0]

def format_job_string(job):
    return (f'#{job['id']} ({job['status']}) '
      f'created at {job['created_at']}')

print(f'Loading latest job:\t{format_job_string(latest_job)}')

latest_timestamp = latest_job['created_at']
latest_job_id = ''

while True:
    pipeline_jobs = get(
        f'{BASE_API_PATH}&started_after={latest_timestamp}',
        headers={'PRIVATE-TOKEN': PRIVATE_TOKEN},
    ).json()

    valid_pipeline_jobs = [job for job in pipeline_jobs 
                            if job['status'] in ['success', 'failed', 'running']]
    
    if not valid_pipeline_jobs:
        print(f'No valid jobs detected. Retrying in {SLEEP_TIME_SECS} seconds...')
        sleep(SLEEP_TIME_SECS)
        continue

    current_pipeline_job = valid_pipeline_jobs[0]
    
    if current_pipeline_job['id'] != latest_job_id:
        print(f'New job detected:\t{format_job_string(current_pipeline_job)}')
        latest_job_id = current_pipeline_job['id']

    match current_pipeline_job['status']:
        case 'success':
            traffic_light_status = 'green'
        case 'failed':
            traffic_light_status = 'red'
        case _:
            traffic_light_status = 'none'
    
    if prev_traffic_light_status != traffic_light_status:
        print(f'Job changed status:\t{format_job_string(current_pipeline_job)}\n'
              f'Traffic light mode changed '
              f'from "{prev_traffic_light_status}" to "{traffic_light_status}".')
        
        run([f'./{traffic_light_status}.sh'])

        print()

    prev_traffic_light_status = traffic_light_status

    sleep(SLEEP_TIME_SECS)
