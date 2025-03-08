<template>
    <div>
        <nav class="navbar">
            <h1 class="logo__text">Onephrase.tech</h1>
            <router-link to="/files" class="nav-link">Файлы</router-link>
        </nav>
        <div class="container">
            <h2>Список файлов</h2>
            <table>
                <thead>
                    <tr>
                        <th>Название файла</th>
                        <th>Действие</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="file in files" :key="file">
                        <td>{{ file }}</td>
                        <td>
                            <button @click="downloadFile(file)">Скачать</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            files: []
        };
    },
    mounted() {
        this.fetchFiles();
    },
    methods: {
        async fetchFiles() {
            try {
                console.log(import.meta.env.VITE_BACKEND_URL);
                const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/products/xlsx_files`);
                const data = await response.json();
                this.files = data.files;
            } catch (error) {
                console.error("Ошибка загрузки списка файлов:", error);
            }
        },
        downloadFile(filename) {
            window.location.href = `${import.meta.env.VITE_BACKEND_URL}/products/download_xlsx/${filename}`;
        }
    }
};
</script>

<style>
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background-color: #333;
    color: white;
}

.nav-link {
    color: white;
    text-decoration: none;
    margin-right: 20px;
}

.container {
    max-width: 600px;
    margin: 20px auto;
    padding: 20px;
    background: #f9f9f9;
    border-radius: 5px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 10px;
    border: 1px solid #ddd;
    text-align: left;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 5px 10px;
    cursor: pointer;
    border-radius: 3px;
}

button:hover {
    background-color: #0056b3;
}
</style>