#!/usr/bin/env python3
"""
Sequential Task Queue System - Chạy lần lượt với delay 1s
"""
import threading
import time
import uuid
from typing import Dict, Any, List, Callable, Optional

# Simple task storage
tasks_db: Dict[str, Dict[str, Any]] = {}
tasks_lock = threading.Lock()

def submit_image_generation_batch(user_id: str, requests_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Submit batch image generation tasks - Chạy tuần tự với delay 1s
    """
    batch_id = str(uuid.uuid4())
    task_ids = []

    # Create all task IDs first
    for i, req in enumerate(requests_list):
        task_id = f"{batch_id}_{i+1}"
        task_ids.append(task_id)

        # Store task info
        with tasks_lock:
            tasks_db[task_id] = {
                'status': 'pending',
                'user_id': user_id,
                'created_at': time.time(),
                'result': None
            }

    # Start sequential processing in background thread
    def process_sequential():
        for i, (task_id, req_data) in enumerate(zip(task_ids, requests_list)):
            # Update status to running
            with tasks_lock:
                tasks_db[task_id]['status'] = 'running'
                tasks_db[task_id]['started_at'] = time.time()

            try:
                print(f"🔄 [SEQUENTIAL] Processing task {task_id} ({i+1}/{len(task_ids)})")

                # Import here to avoid circular imports
                from api_gg_flow.t2i import create_batch_text_to_image

                # Process single request
                result = create_batch_text_to_image(
                    project_id=req_data.get('project_id', 'e3fefbbe-03db-432d-8174-1b837281b6b6'),
                    request_list=[req_data],
                    output_dir="./output_images",
                    verbose=False
                )

                # Update status on completion
                with tasks_lock:
                    if result:
                        tasks_db[task_id]['status'] = 'completed'
                        tasks_db[task_id]['result'] = result
                        print(f"✅ [SEQUENTIAL] Task {task_id} completed successfully")

                        # Update credit on success
                        try:
                            from credit_manager import update_credit_on_completion
                            update_credit_on_completion(user_id, "image_generation", 1)
                        except Exception as e:
                            print(f"⚠️ [CREDIT] Failed to update credit: {e}")
                    else:
                        tasks_db[task_id]['status'] = 'failed'
                        print(f"❌ [SEQUENTIAL] Task {task_id} failed")

                    tasks_db[task_id]['completed_at'] = time.time()

            except Exception as e:
                print(f"❌ [SEQUENTIAL] Task {task_id} error: {e}")
                with tasks_lock:
                    tasks_db[task_id]['status'] = 'failed'
                    tasks_db[task_id]['error'] = str(e)
                    tasks_db[task_id]['completed_at'] = time.time()

            # Delay 1 second between tasks (except for the last one)
            if i < len(task_ids) - 1:
                print(f"⏳ [SEQUENTIAL] Waiting 1 second before next task...")
                time.sleep(1)

        print(f"🎉 [SEQUENTIAL] Batch {batch_id} processing completed!")

    # Start processing in background thread
    processor = threading.Thread(target=process_sequential, daemon=True)
    processor.start()

    return {
        "batch_id": batch_id,
        "task_ids": task_ids,
        "total_tasks": len(task_ids),
        "estimated_completion": len(task_ids) * 35,  # 30s per task + 1s delay + buffer
        "processing_mode": "sequential_with_1s_delay"
    }

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status"""
    with tasks_lock:
        return tasks_db.get(task_id)

def get_batch_status(batch_id: str) -> Dict[str, Any]:
    """Get batch status"""
    with tasks_lock:
        batch_tasks = {
            task_id: task for task_id, task in tasks_db.items()
            if task_id.startswith(f"{batch_id}_")
        }

    if not batch_tasks:
        return {"error": "Batch not found"}

    total = len(batch_tasks)
    completed = sum(1 for t in batch_tasks.values() if t['status'] == 'completed')
    failed = sum(1 for t in batch_tasks.values() if t['status'] == 'failed')
    running = sum(1 for t in batch_tasks.values() if t['status'] == 'running')

    return {
        "batch_id": batch_id,
        "total_tasks": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "progress": (completed + failed) / total if total > 0 else 0,
        "task_statuses": {
            task_id: {
                "status": task['status'],
                "result": task.get('result')
            }
            for task_id, task in batch_tasks.items()
        }
    }

def get_queue_stats() -> Dict[str, Any]:
    """Get queue statistics"""
    with tasks_lock:
        total = len(tasks_db)
        active = sum(1 for t in tasks_db.values() if t['status'] == 'running')
        completed = sum(1 for t in tasks_db.values() if t['status'] == 'completed')
        failed = sum(1 for t in tasks_db.values() if t['status'] == 'failed')
        pending = sum(1 for t in tasks_db.values() if t['status'] == 'pending')

    return {
        "total_tasks": total,
        "active_tasks": active,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "pending_tasks": pending,
        "processing_mode": "sequential_with_1s_delay"
    }

# Dummy task_queue object for compatibility
class DummyQueue:
    def get_task_status(self, task_id):
        return get_task_status(task_id)

    def get_batch_status(self, batch_id):
        return get_batch_status(batch_id)

    def get_queue_stats(self):
        return get_queue_stats()

task_queue = DummyQueue()
