const API_URL = "http://localhost:8000";

export const fetchStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/api/trading/status`);
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching status:", error);
    return null;
  }
};
