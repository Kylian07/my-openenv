import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from openenv_dc.tasks import list_tasks, get_task
from openenv_dc.graders import grade

def check_scores():
    tasks = list_tasks()
    print(f"Checking {len(tasks)} tasks...")
    
    for tid in tasks:
        task = get_task(tid)
        dirty_data = task["dirty_data"]
        # Initial state has no deleted indices
        result = grade(task, dirty_data, set())
        score = result["score"]
        print(f"Task: {tid}")
        print(f"  Initial Score: {score}")
        
        # Check clean data score
        clean_data = task["clean_data"]
        # Clean data needs the correct deleted rows to get 1.0
        rows_to_delete = set(task["rows_to_delete"])
        # We need to simulate the dataset as it would look after deletions?
        # No, the grader takes 'current_data' which matches 'dirty_data' length
        # unless some are deleted.
        # Let's see what happens with clean_data.
        # Note: clean_data in task definition is just the list of cleaned rows.
        # The environment logic usually has the full dataset and some marked deleted.
        
        print("-" * 30)

if __name__ == "__main__":
    check_scores()
