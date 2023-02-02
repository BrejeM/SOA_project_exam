<template>
    <div>
      <h1>SEARCH</h1>
      <form @submit.prevent="search">
        <input v-model="target" placeholder="target term" />
        <br />
        <br />
        <input v-model="subreddits" placeholder="subreddits" type="subreddits" />
        <br />
        <br />
        <button type="submit">Search</button>
      </form>
    </div>
  </template>
  
  <script>
  import { mapGetters, mapMutations } from "vuex";
  
  export default {
    data: () => {
      return {
        target: "",
        subreddits: "",
      };
    },
    methods: {
      ...mapMutations(["setUser", "setToken"]),
      ...mapGetters(["getToken"]),
      async search(e) {
        e.preventDefault();
        const jwttoken = this.getToken()
        const response = await fetch("http://localhost:8082/search", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + jwttoken
          },
          body: JSON.stringify({
            target: this.target,
            subreddits: this.subreddits,
          }),
        });
        const ok_status = await response.status;
        if (ok_status == 200) {
            alert("Search has been scheduled. You'll see it in your dashboard.");
        }
        else {
            alert("Searching has encountered an unexpected error. Try again later!");
        }
        this.$router.push("/dashboard");
      },
    },
  };
  </script>
  
  <style>
  </style>
  