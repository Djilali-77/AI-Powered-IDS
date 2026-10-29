import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Long timeout: free-tier hosts can take ~50s to wake up from sleep
const client = axios.create({ baseURL: API_URL, timeout: 90_000 });

export const getModelInfo = () => client.get("/model-info").then((res) => res.data);

// kind: "benign" | "attack"
export const simulateTraffic = (kind) => client.get(`/simulate/${kind}`).then((res) => res.data);