"""Test/demo script for AutoML Backend API."""
import httpx
import asyncio
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"


async def test_health():
    """Test API health check."""
    print("\n═" * 50)
    print("Testing Health Check")
    print("═" * 50)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_info():
    """Test API info endpoint."""
    print("\n═" * 50)
    print("Testing API Info")
    print("═" * 50)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/info")
        data = response.json()
        print(f"API: {data['name']} v{data['version']}")
        print(f"Available Models: {', '.join(data['available_models'])}")
        print(f"Supported Formats: {', '.join(data['supported_formats'])}")


async def test_upload():
    """Test file upload."""
    print("\n═" * 50)
    print("Testing File Upload")
    print("═" * 50)
    
    # Create a sample CSV file for testing
    sample_csv = Path("sample_data.csv")
    sample_csv.write_text("""age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,target
63,1,3,145,233,1,0,150,0,2.3,0,0,6,0
37,1,2,130,250,0,1,187,0,3.5,0,0,2,0
41,0,1,130,204,0,0,172,0,1.4,2,0,2,0
56,1,1,120,236,0,1,178,0,0.8,2,0,2,0
57,0,0,120,354,0,1,163,1,0.6,2,0,2,0
""")
    
    try:
        async with httpx.AsyncClient() as client:
            with open(sample_csv, 'rb') as f:
                files = {'file': (sample_csv.name, f, 'text/csv')}
                response = await client.post(
                    f"{BASE_URL}/upload",
                    files=files,
                    params={"target_column": "target"}
                )
            
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Filename: {data['filename']}")
            print(f"Size: {data['size_bytes']} bytes")
            print(f"Rows: {data['rows']}, Columns: {len(data['columns'])}")
            print(f"Columns: {', '.join(data['columns'][:5])}...")
            print(f"Temp Path: {data['temp_path']}")
            
            return data['temp_path']
    finally:
        sample_csv.unlink(missing_ok=True)


async def test_pipeline_profile(file_path: str):
    """Test dataset profiling."""
    print("\n═" * 50)
    print("Testing Dataset Profiling")
    print("═" * 50)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/pipeline/profile",
            params={
                "file_path": file_path,
                "target_column": "target"
            }
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Job ID: {data['job_id']}")
        
        profile = data['profile']
        print(f"Dataset Shape: {profile['shape']}")
        print(f"Total Nulls: {profile['total_null_cells']} ({profile['total_null_pct']}%)")
        print(f"Target Type: {profile['target_type']}")
        print(f"Target Balance: {profile['target_balance']}")


async def test_pipeline_audit(file_path: str):
    """Test AI audit."""
    print("\n═" * 50)
    print("Testing AI Audit")
    print("═" * 50)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/pipeline/audit",
            params={
                "file_path": file_path,
                "target_column": "target"
            },
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Job ID: {data['job_id']}")
        print(f"Total Issues: {data['total_issues']}")
        print(f"  - High: {data['high_severity']}")
        print(f"  - Medium: {data['medium_severity']}")
        print(f"  - Low: {data['low_severity']}")
        
        if data['flags']:
            print("\nSample Issues:")
            for flag in data['flags'][:3]:
                print(f"  - [{flag['severity'].upper()}] {flag['id']}: {flag['issue_type']}")
                print(f"    Detail: {flag['detail']}")
                print(f"    Fix: {flag['recommended_fix']}")


async def test_job_status():
    """Test job status endpoint."""
    print("\n═" * 50)
    print("Testing Job Status")
    print("═" * 50)
    
    async with httpx.AsyncClient() as client:
        # List all jobs
        response = await client.get(f"{BASE_URL}/jobs")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total Jobs: {data['total_jobs']}")
        
        if data['jobs']:
            print("\nRecent Jobs:")
            for job in data['jobs'][-3:]:
                print(f"  - {job['job_id']}: {job['status']} ({job['progress']}%)")
                print(f"    Stage: {job['current_stage']}")


async def main():
    """Run all tests."""
    print("\n" + "█" * 50)
    print("AutoML Backend API - Test Suite")
    print("█" * 50)
    
    try:
        # Test health
        await test_health()
        
        # Test info
        await test_info()
        
        # Test upload
        print("\nNote: For full pipeline test, ensure your dataset exists")
        try:
            file_path = await test_upload()
            
            # Test profiling
            await test_pipeline_profile(file_path)
            
            # Test audit
            print("\nNote: Audit requires GROQ_API_KEY to be set")
            try:
                await test_pipeline_audit(file_path)
            except Exception as e:
                print(f"Audit test skipped: {str(e)}")
        except Exception as e:
            print(f"Upload/Profile test skipped: {str(e)}")
        
        # Test job status
        await test_job_status()
        
        print("\n" + "█" * 50)
        print("✓ Test Suite Completed")
        print("█" * 50)
        print("\nNext Steps:")
        print("1. Open http://localhost:8000/docs for Swagger UI")
        print("2. Upload your dataset")
        print("3. Run pipeline with /pipeline/run endpoint")
        print("4. Check job progress with /jobs/{job_id}")
        print("5. Make predictions with /predict endpoint")
        
    except Exception as e:
        print(f"\n✗ Test Error: {str(e)}")
        print("\nMake sure the server is running:")
        print("  uvicorn main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
