#!/usr/bin/env python3
"""
NEOMA P-CAM ROS 2 Hardware Reflex Compliance Node
Shielded execution via RapidAPI Gateway to eliminate 403 bypass errors.
"""

import rclpy
from rclpy.node import Node
import requests
from std_msgs.msg import Float64, String

RAPIDAPI_URL = "https://neoma-p-cam-hyper-physical-control.p.rapidapi.com/v1/robotic-compliance"
RAPIDAPI_HOST = "neoma-p-cam-hyper-physical-control.p.rapidapi.com"

class PCAMComplianceNode(Node):
    def __init__(self):
        super().__init__('pcam_compliance_node')
        
        self.declare_parameter('rapidapi_key', '')
        self.rapidapi_key = self.get_parameter('rapidapi_key').get_parameter_value().string_value
        
        if not self.rapidapi_key:
            self.get_logger().error(
                "RapidAPI Key is REQUIRED! Get your key at: "
                "https://rapidapi.com/shs15199702/api/neoma-p-cam-hyper-physical-control"
            )

        self.damping_pub = self.create_publisher(Float64, '/robot/pcam/optimal_damping', 10)
        self.attestation_pub = self.create_publisher(String, '/robot/pcam/silicon_seal', 10)
        
        self.timer = self.create_timer(0.1, self.query_hardware_reflex)
        self.get_logger().info("NEOMA P-CAM Shielded ROS 2 Node Active.")

    def query_hardware_reflex(self):
        if not self.rapidapi_key:
            return

        headers = {
            "Content-Type": "application/json",
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        payload = {
            "flux_potential_v": 0.082,
            "gradient_velocity": 520,
            "gradient_acceleration": 16000,
            "active_strain": 1.55
        }

        try:
            resp = requests.post(RAPIDAPI_URL, json=payload, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                damping = data["adaptive_control"]["damping_coefficient"]
                seal = data["hardware_seal_id"]
                latency = data["hardware_reflex_ms"]
                
                msg_damping = Float64()
                msg_damping.data = float(damping)
                self.damping_pub.publish(msg_damping)
                
                msg_seal = String()
                msg_seal.data = f"{seal} | {latency:.4f} ms"
                self.attestation_pub.publish(msg_seal)
                
                self.get_logger().info(f"[P-CAM Reflex] Damping: {damping:.4f} | Latency: {latency:.4f} ms")
            elif resp.status_code == 403:
                self.get_logger().error("RapidAPI 403 Forbidden: Invalid or missing API key.")
        except Exception as e:
            self.get_logger().warn(f"[P-CAM Link Error]: {e}")

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

if __name__ == '__main__':
    main()
