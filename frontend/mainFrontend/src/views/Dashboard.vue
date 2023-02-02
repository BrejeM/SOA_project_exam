
<template>
  <div>
    <div v-if="searches !== null && searches.length > 0" v-for="item in searches" v-bind:key="item.id">
      <h2>Search ID: {{ item.id }}</h2>
      <p>Term: {{item.target}}</p>
      <p>Subreddits: {{ item.subreddits }}</p>
      <p >Processed: {{ item.processed }}</p>
      <p v-if="item.processed == true">Trustworthiness: {{item.trust_percentage}}%</p>
    </div>
    <div v-if="searches.length == 0">
      <h2>No search has been performed yet.</h2>
      <div>
            <router-link
            to="/search"
            custom
            v-slot="{ navigate }"
            >
            <button
                @click="navigate"
                role="link"
            >
                Search something
            </button>
            </router-link>
        </div>    
    </div>
  </div>
</template>

<script>

export default {
  computed: {
    searches() {
         console.log()
         return this.$store.getters.getSearches;
      },
  },
  created() {
    this.$store.dispatch('loadSearches');  
  },
  methods: {
    gotoSearch() {
      this.$router.go("/search");
    }
  }
}
</script>

<style></style>
