#!/usr/bin/env python3
"""
NEOMA P-CAM ROS 2 Hardware Reflex Compliance Node
Connects robotics systems directly to the P-CAM physical hardware enclave.
"""

import json
import rclpy
from rclpy.node import Node
import requests
from std_msgs.msg import Float64, String


class PCAMComplianceNode(Node):

    def __init__(self):
        super().__init__("pcam_compliance_node")

        # Parameters
        self.declare_parameter(
            "gateway_url", "https://api.neoma-pcam.com/v1/robotic-compliance"
        )
        self.declare_parameter("rapidapi_key", "")

        self.gateway_url = (
            self.get_parameter("gateway_url")
            .get_parameter_value()
            .string_value
        )
        self.rapidapi_key = (
            self.get_parameter("rapidapi_key")
            .get_parameter_value()
            .string_value
        )

        # Publishers
        self.damping_pub = self.create_publisher(
            Float64, "/robot/pcam/optimal_damping", 10
        )
        self.attestation_pub = self.create_publisher(
            String, "/robot/pcam/silicon_seal", 10
        )

        # Periodic Reflex Evaluation Loop (10 Hz sample test)
        self.timer = self.create_timer(0.1, self.query_hardware_reflex)
        self.get_logger().info(
            "NEOMA P-CAM ROS 2 Hardware Reflex Node Initialized."
        )

    def query_hardware_reflex(self):
        headers = {"Content-Type": "application/json"}
        if self.rapidapi_key:
            headers["X-RapidAPI-Key"] = self.rapidapi_key

        payload = {
            "flux_potential_v": 0.082,
            "gradient_velocity": 520,
            "gradient_acceleration": 16000,
            "active_strain": 1.55,
        }

        try:
            resp = requests.post(
                self.gateway_url, json=payload, headers=headers, timeout=2.0
            )
            if resp.status_code == 200:
                data = resp.json()
                damping = data["adaptive_control"]["damping_coefficient"]
                seal = data["hardware_seal_id"]
                latency = data["hardware_reflex_ms"]

                # Publish to robot controllers
                msg_damping = Float64()
                msg_damping.data = float(damping)
                self.damping_pub.publish(msg_damping)

                msg_seal = String()
                msg_seal.data = f"{seal} | Latency: {latency:.4f} ms"
                self.attestation_pub.publish(msg_seal)

                self.get_logger().info(
                    f"[P-CAM Reflex] Damping: {damping:.4f} | Latency: {latency:.4f} ms | Seal: {seal}"
                )
        except Exception as e:
            self.get_logger().warn(
                f"[P-CAM Reflex Link] Waiting for gateway: {e}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = PCAMComplianceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
