<template>
  <div>
    <div class="register-parent">
      <h4>Register</h4>
      <form @submit.prevent="register" class="register-child">
        <input
          type="username"
          placeholder="Username..."
          v-model="username"
        />
        <input
          type="password"
          placeholder="password..."
          v-model="password"
        />
        <button type="submit">Register</button>
      </form>
    </div>
  </div>
</template>

<script>

export default {
    name: 'Login',
    data() {
        return {
            username: '',
            password: '',
        };
    },
    methods: {
        async register(e) {
            e.preventDefault();
            const response = await fetch("http://localhost:8082/register", {
                method: "POST",
                headers: {
                "Content-Type": "application/json",
                },
                body: JSON.stringify({
                username: this.username,
                password: this.password,
                }),
            });
            const ok_status = await response.status;
            if (ok_status) {
                alert("Successfully registered");
            }
            else {
                alert("Registering failed.");
            }
        
            console.log("Successfully registered.");
            this.$router.push("/login");
            },
        }
};
</script>
<style scoped>
.register-parent {
  max-width: 100%;
  margin-top: 80px;
}
.register-child {
  max-width: 300px;
  display: block;
  margin: 0 auto 0 auto;
}
input {
  width: 200px;
  height: 25px;
  margin-bottom: 10px;
  padding-left: 10px;
}
input:focus {
    outline: none !important;
    border:2px solid #F8874F;
}
button {
  margin-top: 10px;
  width: 216px;
  height: 25px;
  cursor: pointer;
}
</style>