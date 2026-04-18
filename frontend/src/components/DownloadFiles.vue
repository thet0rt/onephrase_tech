<template>
  <div class="page-wrapper">
    <nav class="navbar">
      <router-link to="/create_product" class="logo__text">Onephrase.tech</router-link>
      <router-link to="/files" class="nav-link">Файлы</router-link>
    </nav>

    <div class="main__content">
      <div class="form-header">
        <div>
          <p class="form-eyebrow">Готовые файлы</p>
          <h1 class="form-title">Список файлов</h1>
        </div>
      </div>

      <table class="files-table">
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
              <button class="btn btn--primary btn--sm" @click="downloadFile(file)">Скачать</button>
            </td>
          </tr>
          <tr v-if="files.length === 0">
            <td colspan="2" class="empty-state">Файлов пока нет</td>
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
        const response = await fetch(`api/products/xlsx_files`);
        const data = await response.json();
        this.files = data.files;
      } catch (error) {
        console.error("Ошибка загрузки списка файлов:", error);
      }
    },
    downloadFile(filename) {
      window.location.href = `api/products/download_xlsx/${filename}`;
    }
  }
};
</script>

<style scoped>
.page-wrapper {
  width: 100%;
  min-height: 100vh;
  background: #f5f5f7;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 56px;
  background: #1a1a1a;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo__text {
  color: #fff;
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.nav-link {
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.15s;
}
.nav-link:hover { color: #fff; }

.main__content {
  max-width: 780px;
  margin: 40px auto;
  padding: 36px 40px 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.06);
}

.form-header {
  margin-bottom: 28px;
}

.form-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: #999;
}

.form-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #111;
  letter-spacing: -0.4px;
}

.files-table {
  width: 100%;
  border-collapse: collapse;
}

.files-table th {
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #999;
  padding: 0 16px 12px;
  border-bottom: 1.5px solid #f0f0f0;
}

.files-table td {
  padding: 14px 16px;
  font-size: 14px;
  color: #333;
  border-bottom: 1px solid #f5f5f5;
}

.files-table tr:last-child td {
  border-bottom: none;
}

.files-table tbody tr:hover td {
  background: #fafafa;
}

.empty-state {
  text-align: center;
  color: #aaa;
  padding: 40px 0 !important;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 10px 20px;
  transition: background 0.15s, transform 0.1s;
  white-space: nowrap;
}
.btn:active { transform: scale(0.97); }

.btn--primary { background: #111; color: #fff; }
.btn--primary:hover { background: #333; }

.btn--sm { padding: 6px 14px; font-size: 13px; }
</style>
