const { createServer } = require("./server");
const healthRoutes = require("./routes/health.routes");

const PORT = 3000;

const app = createServer();

app.use(healthRoutes);

app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});