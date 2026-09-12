// Auto-dismiss alerts after 4s
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".alert").forEach(el => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            bsAlert.close();
        }, 4000);
    });

    // Set today as default date for join_date fields
    const dateInputs = document.querySelectorAll('input[name="join_date"]:not([value])');
    const today = new Date().toISOString().split("T")[0];
    dateInputs.forEach(el => { if (!el.value) el.value = today; });
});
