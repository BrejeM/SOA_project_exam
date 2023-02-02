<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <p>
      If you're unsure about a certain object you're interested in, let Reddit help<br>
      You can search for a keyword throughout specified subreddits and obtain a score stating how positively it is viewed by the reddit hivemind.
    </p>
    <h3>Try it now!</h3>
    <div></div>
    <ReactButton @click='onButtonClick()'/>
    <div>
      <div>
            <router-link
            to="/login"
            custom
            v-slot="{ navigate }"
            >
            <button
                @click="navigate"
                role="link"
            >
                Login
            </button>
            </router-link>
        </div>    
    </div>
  </div>
</template>

<script>
import {defineAsyncComponent } from 'vue';
import ReactButton from './ReactButton';

export default {
  name: 'HelloWorld',
  components: { ReactButton },
  props: {
    msg: String
  },
  emits: ['onClick'],
  methods :{
    onButtonClick($event){
      this.$emit("onClick", { fName: this.firstName, lName:this.lastName});
    }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
