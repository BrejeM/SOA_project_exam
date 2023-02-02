import { createStore } from 'vuex'
import axios from 'axios'

export default createStore({
  state: {
    user: null,
    token: null,
  },
  getters: {
    isLoggedIn(state) {
      return !!state.token;
    },
    getToken(state) {
      return state.token;
    },
    getSearches(state) {
      return state.searches;
    }
  },
  mutations: {
    setUser(state, user) {
      state.user = user;
    },
    setToken(state, token) {
      state.token = token;
    },
    setSearches(state, searches) {
      state.searches = searches;
      console.log("set searches");
    }
  },
  actions: {
    async loadSearches ({ commit, state }) {
      try {
            const config = {
                headers: { Authorization: `Bearer ` + state.token }
            };
            console.log(config);
            const response = await axios.get('http://localhost:8082/search', config);
            commit('setSearches', response.data)
            for (let i = 0; i < response.data.length; i++) {
              response.data[i].trust_percentage = Math.round(response.data[i].trust_percentage * 100) / 100;
            }
            console.log(response);
        }
       catch (error) {
          console.log(error);
      }
    }
 },
  modules: {
  }
})
