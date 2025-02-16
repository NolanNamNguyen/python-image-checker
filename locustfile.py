from locust import HttpUser, task, between
import base64


class OCRUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def extract_text(self):
        with open("test_image.png", "rb") as f:
            img = base64.b64encode(f.read()).decode()

        self.client.post(
            "/extract_text",
            json={"image": f"data:image/png;base64,{img}"},
            timeout=60
        )