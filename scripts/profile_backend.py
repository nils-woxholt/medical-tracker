#!/usr/bin/env python3
"""
Performance Profiling Script for SaaS Medical Tracker Backend

This script profiles the FastAPI backend endpoints to measure:
- Response times (p50, p95, p99)
- Throughput (requests per second)
- Memory usage during load
- Database query performance
- Error rates under stress

Usage:
    python scripts/profile_backend.py --help
    python scripts/profile_backend.py --target http://localhost:8000 --duration 60
    python scripts/profile_backend.py --config profiles/load_test_config.json
"""

import asyncio
import time
import json
import statistics
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import psutil
import httpx
import uvloop

# Try to import advanced profiling tools (optional)
try:
    import memory_profiler
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

try:
    import py_spy
    PY_SPY_AVAILABLE = True
except ImportError:
    PY_SPY_AVAILABLE = False


@dataclass
class TestConfig:
    """Configuration for performance testing"""
    target_url: str = "http://localhost:8000"
    duration_seconds: int = 60
    concurrent_users: int = 10
    ramp_up_seconds: int = 10
    endpoints: List[str] = None
    auth_token: Optional[str] = None
    output_format: str = "json"  # json, csv, html
    save_results: bool = True
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = [
                "/api/v1/logs/medications",
                "/api/v1/logs/symptoms", 
                "/api/v1/medications",
                "/api/v1/feel-vs-yesterday",
                "/api/v1/conditions",
                "/api/v1/doctors",
                "/api/v1/passport"
            ]


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class EndpointSummary:
    """Summary statistics for an endpoint"""
    endpoint: str
    method: str
    total_requests: int
    success_rate: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    throughput_rps: float
    error_count: int
    avg_response_size_bytes: float


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float


class PerformanceProfiler:
    """Main profiling orchestrator"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.request_metrics: List[RequestMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        self._auth_headers = {}
        self._setup_auth()
        
    def _setup_auth(self):
        """Setup authentication headers if token provided"""
        if self.config.auth_token:
            self._auth_headers["Authorization"] = f"Bearer {self.config.auth_token}"
    
    async def _get_auth_token(self) -> Optional[str]:
        """Obtain auth token for testing (development only)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.target_url}/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "testpassword"}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("accessToken")
        except Exception as e:
            print(f"⚠️  Could not obtain auth token: {e}")
            print("   Proceeding without authentication...")
        return None
    
    async def _make_request(self, client: httpx.AsyncClient, endpoint: str, method: str = "GET") -> RequestMetrics:
        """Make a single HTTP request and measure metrics"""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        
        try:
            if method.upper() == "POST":
                # Use sample data for POST requests
                sample_data = self._get_sample_data(endpoint)
                response = await client.post(
                    f"{self.config.target_url}{endpoint}",
                    json=sample_data,
                    headers=self._auth_headers,
                    timeout=30.0
                )
            else:
                response = await client.get(
                    f"{self.config.target_url}{endpoint}",
                    headers=self._auth_headers,
                    timeout=30.0
                )
            
            response_time_ms = (time.time() - start_time) * 1000
            response_size = len(response.content) if response.content else 0
            
            return RequestMetrics(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                response_size_bytes=response_size,
                timestamp=timestamp,
                error=None if response.status_code < 400 else f"HTTP {response.status_code}"
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return RequestMetrics(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time_ms=response_time_ms,
                response_size_bytes=0,
                timestamp=timestamp,
                error=str(e)
            )
    
    def _get_sample_data(self, endpoint: str) -> Dict:
        """Generate sample data for POST requests"""
        if "medications" in endpoint and endpoint.endswith("/medications"):
            return {
                "name": "Test Medication",
                "dosage": "10mg",
                "frequency": "daily",
                "notes": "Performance test data"
            }
        elif "logs/medications" in endpoint:
            return {
                "medication_id": "test-med-id",
                "dosage_taken": "10mg",
                "taken_at": datetime.now(timezone.utc).isoformat(),
                "notes": "Performance test log"
            }
        elif "logs/symptoms" in endpoint:
            return {
                "symptom": "Test Symptom",
                "severity": 3,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "notes": "Performance test symptom"
            }
        elif "conditions" in endpoint:
            return {
                "name": "Test Condition", 
                "diagnosed_date": "2023-01-01",
                "severity": "moderate",
                "notes": "Performance test condition"
            }
        elif "doctors" in endpoint:
            return {
                "name": "Dr. Test",
                "specialty": "Internal Medicine",
                "contact_info": "test@example.com",
                "notes": "Performance test doctor"
            }
        return {}
    
    async def _monitor_system_metrics(self):
        """Monitor system resource usage during the test"""
        process = psutil.Process()
        initial_io = process.io_counters()
        
        while True:
            try:
                cpu_percent = psutil.cpu_percent()
                memory_info = psutil.virtual_memory()
                current_io = process.io_counters()
                
                system_metric = SystemMetrics(
                    timestamp=datetime.now(timezone.utc),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_info.percent,
                    memory_used_mb=memory_info.used / (1024 * 1024),
                    disk_io_read_mb=(current_io.read_bytes - initial_io.read_bytes) / (1024 * 1024),
                    disk_io_write_mb=(current_io.write_bytes - initial_io.write_bytes) / (1024 * 1024)
                )
                
                self.system_metrics.append(system_metric)
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"⚠️  Error monitoring system metrics: {e}")
                break
    
    async def _load_test_worker(self, worker_id: int):
        """Individual worker for load testing"""
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            while time.time() - start_time < self.config.duration_seconds:
                for endpoint in self.config.endpoints:
                    # Mix of GET and POST requests
                    methods = ["GET"]
                    if any(path in endpoint for path in ["/medications", "/logs/", "/conditions", "/doctors"]):
                        methods.append("POST")
                    
                    for method in methods:
                        if time.time() - start_time >= self.config.duration_seconds:
                            break
                            
                        metrics = await self._make_request(client, endpoint, method)
                        self.request_metrics.append(metrics)
                        
                        # Small delay to avoid overwhelming the server
                        await asyncio.sleep(0.1)
    
    async def run_load_test(self):
        """Execute the complete load test"""
        print(f"🚀 Starting load test against {self.config.target_url}")
        print(f"   Duration: {self.config.duration_seconds}s")
        print(f"   Concurrent users: {self.config.concurrent_users}")
        print(f"   Endpoints: {len(self.config.endpoints)}")
        
        # Try to get auth token if not provided
        if not self.config.auth_token:
            self.config.auth_token = await self._get_auth_token()
            if self.config.auth_token:
                self._setup_auth()
        
        # Start system monitoring
        monitor_task = asyncio.create_task(self._monitor_system_metrics())
        
        # Start load test workers
        workers = []
        for i in range(self.config.concurrent_users):
            # Stagger worker start times for ramp-up
            delay = (i * self.config.ramp_up_seconds) / self.config.concurrent_users
            await asyncio.sleep(delay)
            
            worker = asyncio.create_task(self._load_test_worker(i))
            workers.append(worker)
        
        # Wait for all workers to complete
        await asyncio.gather(*workers)
        monitor_task.cancel()
        
        print(f"✅ Load test completed. {len(self.request_metrics)} requests made.")
    
    def analyze_results(self) -> Dict:
        """Analyze and summarize performance results"""
        if not self.request_metrics:
            return {"error": "No request metrics collected"}
        
        # Group metrics by endpoint and method
        endpoint_groups = {}
        for metric in self.request_metrics:
            key = f"{metric.method} {metric.endpoint}"
            if key not in endpoint_groups:
                endpoint_groups[key] = []
            endpoint_groups[key].append(metric)
        
        # Calculate summary statistics for each endpoint
        endpoint_summaries = []
        for key, metrics in endpoint_groups.items():
            method, endpoint = key.split(" ", 1)
            
            response_times = [m.response_time_ms for m in metrics]
            successful_requests = [m for m in metrics if m.status_code < 400 and m.error is None]
            
            if response_times:
                summary = EndpointSummary(
                    endpoint=endpoint,
                    method=method,
                    total_requests=len(metrics),
                    success_rate=(len(successful_requests) / len(metrics)) * 100,
                    avg_response_time_ms=statistics.mean(response_times),
                    p50_response_time_ms=statistics.median(response_times),
                    p95_response_time_ms=self._percentile(response_times, 0.95),
                    p99_response_time_ms=self._percentile(response_times, 0.99),
                    max_response_time_ms=max(response_times),
                    min_response_time_ms=min(response_times),
                    throughput_rps=len(successful_requests) / self.config.duration_seconds,
                    error_count=len(metrics) - len(successful_requests),
                    avg_response_size_bytes=statistics.mean([m.response_size_bytes for m in metrics])
                )
                endpoint_summaries.append(summary)
        
        # Overall statistics
        total_requests = len(self.request_metrics)
        successful_requests = [m for m in self.request_metrics if m.status_code < 400 and m.error is None]
        all_response_times = [m.response_time_ms for m in self.request_metrics]
        
        overall_stats = {
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "success_rate": (len(successful_requests) / total_requests) * 100 if total_requests > 0 else 0,
            "overall_throughput_rps": len(successful_requests) / self.config.duration_seconds,
            "avg_response_time_ms": statistics.mean(all_response_times) if all_response_times else 0,
            "p95_response_time_ms": self._percentile(all_response_times, 0.95) if all_response_times else 0,
            "max_response_time_ms": max(all_response_times) if all_response_times else 0
        }
        
        # System metrics summary
        system_stats = {}
        if self.system_metrics:
            system_stats = {
                "avg_cpu_percent": statistics.mean([m.cpu_percent for m in self.system_metrics]),
                "max_cpu_percent": max([m.cpu_percent for m in self.system_metrics]),
                "avg_memory_percent": statistics.mean([m.memory_percent for m in self.system_metrics]),
                "max_memory_mb": max([m.memory_used_mb for m in self.system_metrics]),
                "total_disk_read_mb": max([m.disk_io_read_mb for m in self.system_metrics]),
                "total_disk_write_mb": max([m.disk_io_write_mb for m in self.system_metrics])
            }
        
        return {
            "test_config": asdict(self.config),
            "overall_stats": overall_stats,
            "system_stats": system_stats,
            "endpoint_summaries": [asdict(summary) for summary in endpoint_summaries],
            "test_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def save_results(self, results: Dict, output_dir: str = "docs/perf"):
        """Save results to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.config.output_format == "json":
            filename = f"backend_performance_{timestamp}.json"
            with open(output_path / filename, "w") as f:
                json.dump(results, f, indent=2, default=str)
        
        elif self.config.output_format == "csv":
            filename = f"backend_performance_{timestamp}.csv"
            self._save_csv_results(results, output_path / filename)
        
        elif self.config.output_format == "html":
            filename = f"backend_performance_{timestamp}.html"
            self._save_html_results(results, output_path / filename)
        
        print(f"📊 Results saved to {output_path / filename}")
        return output_path / filename
    
    def _save_csv_results(self, results: Dict, filepath: Path):
        """Save results in CSV format"""
        import csv
        
        with open(filepath, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            
            # Overall stats
            writer.writerow(["Metric", "Value"])
            for key, value in results["overall_stats"].items():
                writer.writerow([key, value])
            
            writer.writerow([])  # Empty row
            
            # Endpoint summaries
            if results["endpoint_summaries"]:
                headers = list(results["endpoint_summaries"][0].keys())
                writer.writerow(headers)
                
                for summary in results["endpoint_summaries"]:
                    writer.writerow([summary[key] for key in headers])
    
    def _save_html_results(self, results: Dict, filepath: Path):
        """Save results in HTML format"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backend Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Backend Performance Report</h1>
            <p>Generated: {results['test_timestamp']}</p>
            
            <h2>Overall Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for key, value in results["overall_stats"].items():
            html_content += f"<tr><td class='metric'>{key}</td><td>{value}</td></tr>"
        
        html_content += """
            </table>
            
            <h2>Endpoint Performance</h2>
            <table>
                <tr>
                    <th>Endpoint</th><th>Method</th><th>Requests</th>
                    <th>Success Rate %</th><th>Avg Response (ms)</th>
                    <th>P95 Response (ms)</th><th>Throughput (RPS)</th>
                </tr>
        """
        
        for summary in results["endpoint_summaries"]:
            html_content += f"""
                <tr>
                    <td>{summary['endpoint']}</td>
                    <td>{summary['method']}</td>
                    <td>{summary['total_requests']}</td>
                    <td>{summary['success_rate']:.1f}</td>
                    <td>{summary['avg_response_time_ms']:.1f}</td>
                    <td>{summary['p95_response_time_ms']:.1f}</td>
                    <td>{summary['throughput_rps']:.1f}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(filepath, "w") as f:
            f.write(html_content)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Profile SaaS Medical Tracker backend performance")
    parser.add_argument("--target", default="http://localhost:8000", help="Target server URL")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--ramp-up", type=int, default=10, help="Ramp-up time in seconds")
    parser.add_argument("--auth-token", help="JWT token for authentication")
    parser.add_argument("--config", help="JSON config file path")
    parser.add_argument("--output-format", choices=["json", "csv", "html"], default="json", help="Output format")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    parser.add_argument("--endpoints", nargs="+", help="Specific endpoints to test")
    
    args = parser.parse_args()
    
    # Load config from file if provided
    if args.config:
        with open(args.config, "r") as f:
            config_data = json.load(f)
        config = TestConfig(**config_data)
    else:
        config = TestConfig(
            target_url=args.target,
            duration_seconds=args.duration,
            concurrent_users=args.users,
            ramp_up_seconds=args.ramp_up,
            auth_token=args.auth_token,
            output_format=args.output_format,
            save_results=not args.no_save,
            endpoints=args.endpoints
        )
    
    # Use uvloop for better async performance
    if sys.platform != "win32":
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # Run the profiler
    profiler = PerformanceProfiler(config)
    
    async def run_test():
        await profiler.run_load_test()
        results = profiler.analyze_results()
        
        # Print summary
        print("\n📈 Performance Summary:")
        print(f"   Total requests: {results['overall_stats']['total_requests']}")
        print(f"   Success rate: {results['overall_stats']['success_rate']:.1f}%")
        print(f"   Average response time: {results['overall_stats']['avg_response_time_ms']:.1f}ms")
        print(f"   P95 response time: {results['overall_stats']['p95_response_time_ms']:.1f}ms")
        print(f"   Throughput: {results['overall_stats']['overall_throughput_rps']:.1f} RPS")
        
        if config.save_results:
            profiler.save_results(results)
        
        return results
    
    try:
        results = asyncio.run(run_test())
        
        # Performance assertions (warnings)
        if results['overall_stats']['p95_response_time_ms'] > 300:
            print("⚠️  Warning: P95 response time exceeds 300ms target")
        
        if results['overall_stats']['success_rate'] < 99:
            print("⚠️  Warning: Success rate below 99%")
        
        print("✅ Performance profiling completed successfully")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()