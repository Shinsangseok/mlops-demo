import os
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parent.parent


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return

        try:
            quality = json.loads(
                (ROOT / "reports/quality_report.json").read_text()
            )
            drift = json.loads(
                (ROOT / "reports/drift_report.json").read_text()
            )

            lines = [
                "# TYPE feature_quality_pass gauge",
                f"feature_quality_pass {int(quality['passed'])}",
                "# TYPE feature_quality_null_count gauge",
            ]

            for feature, count in quality["null_counts"].items():
                lines.append(
                    f'feature_quality_null_count{{feature="{feature}"}} {count}'
                )

            lines.extend([
                "# TYPE feature_quality_negative_session_duration gauge",
                "feature_quality_negative_session_duration "
                + str(quality["negative_session_duration"]),
                "# TYPE feature_quality_age_out_of_range gauge",
                "feature_quality_age_out_of_range "
                + str(quality["age_out_of_range"]),
                "# TYPE feature_drift_psi gauge",
            ])

            for feature, result in drift["features"].items():
                if result["psi"] is not None:
                    lines.append(
                        f'feature_drift_psi{{feature="{feature}"}} '
                        f'{result["psi"]}'
                    )

            lines.extend([
                "# TYPE feature_drift_detected gauge",
                f"feature_drift_detected {int(drift['has_drift'])}",
            ])

            body = ("\n".join(lines) + "\n").encode()

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.send_error(500, str(exc))


if __name__ == "__main__":
    host = os.getenv("METRICS_HOST", "127.0.0.1")
    port = int(os.getenv("METRICS_PORT", "9101"))

    print(
        f"Metrics Exporter: http://{host}:{port}/metrics",
        flush=True,
    )

    HTTPServer((host, port), MetricsHandler).serve_forever()
