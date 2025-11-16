# Troubleshooting Guide

## Common Issues and Solutions

### 1. ReadTimeoutError: Read timeout on endpoint URL

**Error:**
```
botocore.exceptions.ReadTimeoutError: Read timeout on endpoint URL:
"https://bedrock-runtime.us-east-1.amazonaws.com/model/us.anthropic.claude-sonnet-4-5-20250929-v1%3A0/invoke"
```

**Cause:** The AWS Bedrock API call is taking longer than the default timeout (usually 60 seconds).

**Solution:** We've increased the timeout to 15 minutes (900 seconds) in `bedrock_llm.py`.

**What was changed:**
```python
# Extended timeout configuration
bedrock_config = Config(
    read_timeout=900,  # 15 minutes
    connect_timeout=60,  # 1 minute
    retries={'max_attempts': 3, 'mode': 'adaptive'}
)
```

**If still timing out:**

1. **Reduce max_tokens** - Lower the output length:
   ```bash
   python -m aws_diagram_generator.cli \
     --max-tokens 8192 \
     --config your_config.yaml
   ```

2. **Use a faster model** - Try Nova Pro instead:
   ```bash
   python -m aws_diagram_generator.cli \
     --model-id us.amazon.nova-pro-v1:0 \
     --config your_config.yaml
   ```

3. **Process fewer targets** - Split your config into smaller batches

---

### 2. ThrottlingException: Too many requests

**Error:**
```
ThrottlingException: Too many requests, please wait before trying again.
```

**Cause:** Hitting AWS Bedrock rate limits.

**Solutions:**

1. **Wait and retry** - Rate limits reset after ~1 minute
2. **Use inference profiles** - Higher quotas (already the default for Claude 4.5)
3. **Check quotas:**
   ```bash
   aws service-quotas list-service-quotas \
     --service-code bedrock \
     --region us-east-1 \
     --query 'Quotas[?contains(QuotaName, `Claude`)].{Name:QuotaName, Value:Value}' \
     --output table
   ```

---

### 3. ValidationException: Invocation of model ID ... isn't supported

**Error:**
```
ValidationException: Invocation of model ID anthropic.claude-sonnet-4-5-20250929-v1:0
with on-demand throughput isn't supported. Retry your request with the ID or ARN of
an inference profile that contains this model.
```

**Cause:** Newer models require inference profiles.

**Solution:** Use the inference profile format with `us.` prefix:

**Wrong:** `anthropic.claude-sonnet-4-5-20250929-v1:0`
**Correct:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0`

This is already configured as the default in the code.

---

### 4. Model use case details have not been submitted

**Error:**
```
Model use case details have not been submitted for this account. Fill out the
Anthropic use case details form before using the model.
```

**Cause:** First-time Anthropic model usage requires use case approval.

**Solution:**

1. Go to AWS Bedrock Console: https://console.aws.amazon.com/bedrock/
2. Navigate to **Model access**
3. Click **Manage model access**
4. Find **Anthropic** section
5. Click **Edit** or **Submit use case details**
6. Fill out:
   - **Use case:** "Automated generation of AWS infrastructure architecture diagrams and technical documentation"
   - **Industry:** IT/Technology
   - **Expected usage:** Medium
7. Submit and wait 5-15 minutes for approval

---

### 5. Output Truncated / Incomplete

**Symptom:** The generated markdown file ends abruptly mid-sentence.

**Cause:** Token limit reached before completion.

**Solution:** Increase `max_tokens`:

```bash
python -m aws_diagram_generator.cli \
  --max-tokens 32000 \
  --config your_config.yaml
```

**Default is now 16,384** which should handle most cases.

---

### 6. Import Errors

**Error:**
```
ImportError: cannot import name 'BedrockLLM'
```

**Solution:** Ensure you have all files:
- `aws_diagram_generator/bedrock_llm.py` exists
- All dependencies installed: `pip install -r requirements.txt`

---

### 7. Poor Quality Diagrams

**Symptom:** PlantUML diagrams don't use AWS icons or have wrong structure.

**Solutions:**

1. **Use Claude Sonnet 4.5** (default) - Best for PlantUML
2. **Check the prompts** were updated (analyst and draftsman tasks in `core.py`)
3. **Increase max_tokens** to allow detailed diagrams
4. **Review the scan data** - Ensure all resources were discovered

See `IMPROVING_DIAGRAMS.md` for detailed guide.

---

### 8. AWS Credentials Issues

**Error:**
```
NoCredentialsError: Unable to locate credentials
```

**Solutions:**

1. **Configure AWS CLI:**
   ```bash
   aws configure
   ```

2. **Set environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **Use IAM role** (if running on EC2)

---

### 9. SSL Certificate Errors (CrewAI Telemetry)

**Error:**
```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: unable to get local issuer certificate'
```

**Cause:** CrewAI trying to connect to app.crewai.com for telemetry.

**Solution:** Already disabled in code with:
```python
os.environ['OTEL_SDK_DISABLED'] = 'true'
```

This warning can be safely ignored.

---

## Performance Optimization

### For Large Infrastructures

If you have many resources (50+):

1. **Use higher max_tokens:**
   ```bash
   --max-tokens 32000
   ```

2. **Increase timeouts** (already done in BedrockLLM)

3. **Process in batches** - Split config into multiple files

4. **Use faster model for initial testing:**
   ```bash
   --model-id us.amazon.nova-pro-v1:0
   ```

### For Faster Iterations

During development/testing:

1. **Lower max_tokens** for speed:
   ```bash
   --max-tokens 8192
   ```

2. **Higher temperature** for variety:
   ```bash
   --temperature 0.3
   ```

3. **Test with single target** first

---

## Checking Logs

View detailed logs:

```bash
tail -f aws_diagram_generator.log
```

Look for:
- Resource discovery counts
- API call failures
- Task completion status

---

## Getting Help

1. **Check documentation:**
   - `README.md` - General usage
   - `CLAUDE_SONNET_4_5_SETUP.md` - Model setup
   - `IMPROVING_DIAGRAMS.md` - Diagram quality
   - `TROUBLESHOOTING.md` - This file

2. **Check AWS Bedrock status:**
   - https://status.aws.amazon.com/

3. **Verify model access:**
   ```bash
   aws bedrock list-foundation-models --region us-east-1 \
     --query 'modelSummaries[?contains(modelId, `claude`)].modelId'
   ```

4. **Test Bedrock connectivity:**
   ```bash
   aws bedrock get-foundation-model \
     --model-identifier us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
     --region us-east-1
   ```
