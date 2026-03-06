# AWS EC2 Deployment Guide (Student Account)

Deploy EduPredict Pro to your own AWS server - **free for 12 months** with student account.

---

## Quick Start (5 minutes)

### Step 1: Launch EC2 Instance

1. **Log into AWS Console:** https://aws.amazon.com/console
2. **Go to EC2 → Instances → Launch Instances**
3. **Name:** `EduPredict-Pro`
4. **AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)
5. **Instance type:** t2.micro (Free tier eligible ✓)
6. **Key pair:** Create new or use existing (download .pem file)
7. **Network settings:**
   - Create security group
   - **Allow SSH (port 22)** from your IP
   - **Allow Custom TCP (port 8501)** from anywhere (0.0.0.0/0) ← **IMPORTANT**
8. **Storage:** 8 GB (default)
9. **Click "Launch instance"**

### Step 2: Connect to Instance

```bash
# On your local machine, in terminal:
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR-EC2-PUBLIC-IP
```

**Find your public IP:** EC2 Console → Instances → Click instance → "Public IPv4 address"

### Step 3: Deploy App (Run on EC2)

Once connected to your EC2 instance via SSH, run:

```bash
curl -fsSL https://raw.githubusercontent.com/GaneshMunagala714/Edupredict-Pro/main/aws-deploy.sh | bash
```

**Or manually:**
```bash
# Update system
sudo apt-get update -y

# Install Python
sudo apt-get install -y python3 python3-pip git

# Clone repo
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

# Install dependencies
pip3 install -r requirements.txt

# Run app
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
```

### Step 4: Access Your App

**Your app is live at:**
```
http://YOUR-EC2-PUBLIC-IP:8501
```

**Example:** `http://3.84.123.45:8501`

---

## Keep App Running 24/7 (Auto-restart)

If you used the `aws-deploy.sh` script, the app is already set up as a service and will auto-start if the server reboots.

**Check status:**
```bash
sudo systemctl status edupredict
```

**View logs:**
```bash
sudo journalctl -u edupredict -f
```

**Restart:**
```bash
sudo systemctl restart edupredict
```

---

## Cost

| Service | Cost |
|---------|------|
| t2.micro EC2 | **FREE** for 12 months (750 hours/month) |
| Data transfer | First 1 GB/month free |
| **Total** | **$0 for first year** |

After 12 months: ~$8/month if you keep it running 24/7.

---

## Security Group Setup (Critical!)

Your security group must have these inbound rules:

| Type | Protocol | Port Range | Source | Purpose |
|------|----------|------------|--------|---------|
| SSH | TCP | 22 | Your IP | Connect to server |
| Custom TCP | TCP | 8501 | 0.0.0.0/0 | Streamlit app |

**To edit security group:**
1. EC2 Console → Security Groups
2. Find your instance's security group
3. Edit inbound rules
4. Add rule: Custom TCP, port 8501, source 0.0.0.0/0
5. Save

---

## Troubleshooting

### App not loading?
1. Check security group allows port 8501
2. Check app is running: `sudo systemctl status edupredict`
3. Check logs: `sudo journalctl -u edupredict`

### Permission denied on SSH?
```bash
chmod 400 your-key.pem
```

### Port already in use?
```bash
sudo lsof -ti:8501 | xargs sudo kill -9
```

---

## Your App is Now

- ✅ Running on your own AWS server
- ✅ Accessible 24/7 (as long as EC2 is running)
- ✅ Free for 12 months
- ✅ No Streamlit Cloud subscription needed
- ✅ Permanent URL (until you stop the instance)

**Landing page:** `https://GaneshMunagala714.github.io/Edupredict-Pro`  
**Live app:** `http://YOUR-EC2-IP:8501`

---

*Deploy once, use forever (or at least 12 months free)*
