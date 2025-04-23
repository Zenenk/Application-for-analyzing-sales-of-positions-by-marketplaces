import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  headers: {
    'Authorization': 'Bearer your_api_token_here'
  }
});

export const getItems = async () => {
  const response = await API.get('/items');
  return response.data;
};
