# Deployment Guide - Vercel

## Prerequisites

1. **Vercel CLI** installed:
   ```bash
   npm install -g vercel
   ```

2. **API Keys** ready:
   - Google Gemini API Key: https://makersuite.google.com/app/apikey
   - Pinecone API Key: https://app.pinecone.io/

3. **Pinecone Index** populated with book content (run `backend/ingest.py` first)

## Step 1: Prepare Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
GOOGLE_API_KEY=your_actual_google_api_key
PINECONE_API_KEY=your_actual_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=rag-chatbot-768
```

## Step 2: Populate Pinecone Index (One-time setup)

If you haven't already populated your Pinecone index with the book content:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY=your_key
export PINECONE_API_KEY=your_key
export PINECONE_ENVIRONMENT=us-east-1-aws
export PINECONE_INDEX_NAME=rag-chatbot-768

# Run ingestion script
python backend/ingest.py
```

This will:
- Load all `.md` and `.mdx` files from the `docs/` directory
- Chunk them into smaller pieces
- Generate embeddings using Google's text-embedding-004
- Upload to Pinecone index

## Step 3: Test Locally (Optional)

Install Vercel CLI and test locally:

```bash
# Install dependencies
npm install

# Run Vercel dev server
vercel dev
```

Visit `http://localhost:3000` and test the chatbot.

## Step 4: Deploy to Vercel

### Option A: Deploy via CLI

```bash
# Login to Vercel
vercel login

# Deploy (first time)
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No
# - Project name? (accept default or customize)
# - Directory? ./ (press Enter)
# - Override settings? No

# Add environment variables
vercel env add GOOGLE_API_KEY
vercel env add PINECONE_API_KEY
vercel env add PINECONE_ENVIRONMENT
vercel env add PINECONE_INDEX_NAME

# Deploy to production
vercel --prod
```

### Option B: Deploy via Vercel Dashboard

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure project:
   - Framework Preset: Other
   - Build Command: `npm run build`
   - Output Directory: `build`
4. Add Environment Variables:
   - `GOOGLE_API_KEY`
   - `PINECONE_API_KEY`
   - `PINECONE_ENVIRONMENT`
   - `PINECONE_INDEX_NAME`
5. Click "Deploy"

## Step 5: Verify Deployment

After deployment:

1. Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
2. Open the chatbot widget (bottom-right corner)
3. Ask a question about the book content
4. Verify the AI responds with relevant information

## Troubleshooting

### Issue: "AI is unavailable"

**Check:**
- Environment variables are set correctly in Vercel dashboard
- Pinecone index exists and has data
- API keys are valid

**View logs:**
```bash
vercel logs
```

### Issue: "Cannot reach backend"

**Check:**
- `/api/chat.py` is deployed (check Vercel Functions tab)
- CORS headers are working
- Browser console for errors

### Issue: Slow responses

**Note:** First request may be slow (cold start). Subsequent requests should be faster due to caching.

## Architecture

```
Frontend (Docusaurus)
    ↓
/api/chat.py (Vercel Serverless Function)
    ↓
Google Gemini AI + Pinecone Vector DB
```

## Cost Considerations

- **Vercel**: Free tier includes 100GB bandwidth, serverless functions
- **Google Gemini**: Free tier available (check current limits)
- **Pinecone**: Free tier includes 1 index, 100K vectors

## Next Steps

After successful deployment:
1. Monitor usage in Vercel dashboard
2. Set up custom domain (optional)
3. Configure analytics (optional)
4. Add more features to chatbot (optional)
