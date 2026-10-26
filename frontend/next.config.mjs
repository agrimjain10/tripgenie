/** Keep cloud API calls on the app's own origin. */
const backend = (process.env.BACKEND_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export default {
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }];
  },
};
