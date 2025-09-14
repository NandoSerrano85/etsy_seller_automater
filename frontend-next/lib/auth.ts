export async function getOAuthData() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/oauth-data`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching OAuth data:', error);
    throw error;
  }
}