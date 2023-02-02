import { createApp,defineAsyncComponent } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import axios from 'axios'

console.log("entry");
const Button = defineAsyncComponent(() => import('Remote/Nav'));

const app = createApp(App);

app.component('ahaha', Button);


app.use(store).use(router).mount('#app');
