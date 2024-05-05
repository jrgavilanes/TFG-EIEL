import { ref, computed, reactive } from 'vue'
import { defineStore } from 'pinia'

import { useRouter } from 'vue-router';


export const useUserStore = defineStore('userStore', () => {

  const router = useRouter();

  const data = reactive({
    id: '',
    username: '',
    role: '',
    token: '',
    municipality: '',
    is_desktop: true,
  })

  const user = computed(() => {
    return {
      id: data.id,
      username: data.username,
      role: data.role,
      token: data.token,
      municipality: data.municipality,
      is_desktop: data.is_desktop,
    }
  });

  const login = (jwt) => {

    localStorage.setItem('token', jwt)

    const tokenParts = jwt.split('.');
    const decodedPayload = atob(tokenParts[1]);
    
    const payloadObj = JSON.parse(decodedPayload);
    data.id = payloadObj.id;
    data.username = payloadObj.username;
    data.role = payloadObj.role;
    data.token = jwt;
    data.municipality = payloadObj.municipality;
    data.is_desktop = payloadObj.is_desktop;

    router.replace({ name: 'MapView' })

  }

  const logout = () => {
    localStorage.removeItem('token');
    data.id = '';
    data.username = '';
    data.role = '';
    data.token = '';
    data.municipality = '';
    data.is_desktop = true;

    // router.replace({ name: 'Login' })
    window.location.href = '/login';
  }
  
  const loadToken = () => {
    const jwt = localStorage.getItem('token');
    if (jwt) {
      login(jwt);      
      return
    }
    router.replace({ name: 'Login' })
  }

  return {
    login,
    loadToken,
    logout,
    user,
  }

})
