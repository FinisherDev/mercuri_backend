from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1,5)

    @task
    def place_order(self):
        self.client.post("/api/delivery/orders/", json = {
            "status": "pending",
            "item_type": "Small",
            "item_cost": "500.00",
            "pickup_latitude": 6.7,
            "pickup_longitude": 6.7,
            "dropoff_latitude": 7.1,
            "dropoff_longitude": 7.1,
        })