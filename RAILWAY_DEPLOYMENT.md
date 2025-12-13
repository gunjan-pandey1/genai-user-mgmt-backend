# Railway Deployment Guide - Backend

This guide will help you deploy the GenAI User Management Backend to Railway.com.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **MongoDB Database**: You'll need a MongoDB instance (Railway provides MongoDB as a plugin)

## Environment Variables Required

The following environment variables must be set in Railway:

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `DB_NAME` | Database name | `genai_crud` |
| `GROQ_API_KEY` | Groq API key for AI features | `gsk_...` |
| `PORT` | Port (automatically set by Railway) | `8000` |

## Deployment Steps

### Option 1: Deploy from GitHub (Recommended)

1. **Login to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Login" and authenticate with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select the `genai-user-mgmt-backend` directory

3. **Add MongoDB Database**
   - In your project, click "New"
   - Select "Database" → "Add MongoDB"
   - Railway will automatically provision a MongoDB instance
   - Copy the `MONGO_URL` from the MongoDB service variables

4. **Configure Environment Variables**
   - Click on your backend service
   - Go to "Variables" tab
   - Add the following variables:
     ```
     MONGODB_URL=<paste the MONGO_URL from MongoDB service>
     DB_NAME=genai_crud
     GROQ_API_KEY=<your-groq-api-key>
     ```

5. **Deploy**
   - Railway will automatically detect the Dockerfile
   - The deployment will start automatically
   - Wait for the build to complete (usually 2-5 minutes)

6. **Get Your Service URL**
   - Once deployed, go to "Settings" tab
   - Under "Networking", click "Generate Domain"
   - Your backend will be available at: `https://your-app.railway.app`

### Option 2: Deploy with Railway CLI

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login**
   ```bash
   railway login
   ```

3. **Initialize Project**
   ```bash
   cd genai-user-mgmt-backend
   railway init
   ```

4. **Add MongoDB**
   ```bash
   railway add --plugin mongodb
   ```

5. **Set Environment Variables**
   ```bash
   railway variables set MONGODB_URL=<mongodb-url>
   railway variables set DB_NAME=genai_crud
   railway variables set GROQ_API_KEY=<your-groq-api-key>
   ```

6. **Deploy**
   ```bash
   railway up
   ```

## Docker Configuration

The backend uses a multi-stage Dockerfile optimized for production:

- **Stage 1 (Builder)**: Installs build dependencies and Python packages
- **Stage 2 (Production)**: Creates a minimal production image
- **Security**: Runs as non-root user
- **Health Check**: Includes health endpoint at `/health`
- **Port**: Uses Railway's `PORT` environment variable

## Testing the Deployment

Once deployed, test your endpoints:

1. **Health Check**
   ```bash
   curl https://your-app.railway.app/health
   ```
   Expected response:
   ```json
   {"status": "healthy", "service": "genai-user-mgmt-backend"}
   ```

2. **Root Endpoint**
   ```bash
   curl https://your-app.railway.app/
   ```
   Expected response:
   ```json
   {"message": "GenAI CRUD Backend is running"}
   ```

3. **API Documentation**
   - Visit: `https://your-app.railway.app/docs`
   - This will show the FastAPI Swagger UI

## Monitoring

Railway provides built-in monitoring:

- **Logs**: View real-time logs in the Railway dashboard
- **Metrics**: CPU, Memory, and Network usage
- **Health Checks**: Automatic health monitoring

## Troubleshooting

### Build Fails

- Check the build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Dockerfile syntax

### Application Crashes

- Check application logs
- Verify environment variables are set correctly
- Ensure MongoDB connection string is valid

### Connection Issues

- Verify MongoDB is running
- Check if MONGODB_URL is correct
- Ensure firewall rules allow Railway IPs

## Updating the Deployment

Railway automatically redeploys when you push to your GitHub repository:

1. Make changes to your code
2. Commit and push to GitHub
3. Railway will automatically detect changes and redeploy

## Cost Optimization

- Railway offers $5 free credit per month
- Monitor your usage in the Railway dashboard
- Consider using Railway's sleep mode for development environments

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- GitHub Issues: Create an issue in your repository
