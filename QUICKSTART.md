# Quick Start - Deploy to Vercel

## ✅ What's Been Done

Your project is now ready for Vercel deployment with:
- ✅ Backend converted to Vercel Python serverless function (`/api/chat.py`)
- ✅ Frontend already configured to call `/api/chat`
- ✅ `vercel.json` configured for Python runtime
- ✅ `requirements.txt` with all dependencies
- ✅ `.env.example` template created

## 🚀 Deployment Steps

### Step 1: Set Up Environment Variables

You need these API keys:

1. **Google Gemini API Key**: Get from https://makersuite.google.com/app/apikey
2. **Pinecone API Key**: Get from https://app.pinecone.io/

### Step 2: Ensure Pinecone Index is Populated

**IMPORTANT**: Before deploying, make sure your Pinecone index has the book content.

If not done yet:

```bash
# Create .env file with your keys
cp .env.example .env
# Edit .env and add your actual API keys

# Install Python dependencies
pip install -r requirements.txt

# Run ingestion script to populate Pinecone
python backend/ingest.py
```

This will load all your book content from the `docs/` folder into Pinecone.

### Step 3: Push to GitHub

```bash
# Check current status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Migrate backend to Vercel serverless functions"

# Push to GitHub
git push origin main
```

### Step 4: Deploy to Vercel

#### Option A: Via Vercel Dashboard (Easiest)

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - Framework: Other
   - Build Command: `npm run build`
   - Output Directory: `build`
4. Add Environment Variables:
   - `GOOGLE_API_KEY` = your_google_api_key
   - `PINECONE_API_KEY` = your_pinecone_api_key
   - `PINECONE_ENVIRONMENT` = us-east-1-aws (or your region)
   - `PINECONE_INDEX_NAME` = rag-chatbot-768
5. Click **Deploy**

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Add environment variables
vercel env add GOOGLE_API_KEY
vercel env add PINECONE_API_KEY
vercel env add PINECONE_ENVIRONMENT
vercel env add PINECONE_INDEX_NAME

# Deploy to production
vercel --prod
```

### Step 5: Test Your Deployment

1. Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
2. Click the chatbot icon (bottom-right)
3. Ask: "What is Physical AI?"
4. Verify the AI responds with content from your book

## 🔧 Troubleshooting

### "AI is unavailable"
- Check environment variables in Vercel dashboard
- Verify Pinecone index exists and has data
- Check Vercel function logs: `vercel logs`

### Slow first response
- Normal! First request has cold start (~5-10 seconds)
- Subsequent requests are faster

### CORS errors
- Already configured in `/api/chat.py`
- Check browser console for details

## 📁 Project Structure

```
Physical-AI-and-Humanoid-Robotics-book-with-chatbot/
├── api/
│   └── chat.py              # Vercel serverless function (RAG chatbot)
├── backend/
│   ├── ingest.py            # Script to populate Pinecone
│   ├── main2.py             # Original FastAPI (reference only)
│   └── requirements.txt     # Backend dependencies
├── docs/                    # Book content (Markdown/MDX)
├── src/
│   └── components/
│       └── ChatWidget.tsx   # Frontend chatbot UI
├── vercel.json              # Vercel configuration
├── requirements.txt         # Python dependencies for Vercel
├── .env.example             # Environment variables template
└── DEPLOYMENT.md            # Detailed deployment guide
```

## 🎯 Next Steps

1. **Now**: Push code to GitHub
2. **Then**: Deploy to Vercel (follow Step 4 above)
3. **Finally**: Test the chatbot on your live site

## 💡 Tips

- Keep your API keys secret (never commit `.env` file)
- Monitor usage in Vercel dashboard
- Check Pinecone dashboard for vector database stats
- Free tiers available for all services (Vercel, Gemini, Pinecone)

---

**Ready to deploy?** Follow Step 3 above to push to GitHub, then I'll help you deploy to Vercel!
