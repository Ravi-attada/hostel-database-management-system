file = "templates/edit_tenant.html"
with open(file, "r", encoding="utf-8") as f:
    content = f.read()

js_append = """
<script>
document.addEventListener("DOMContentLoaded", function() {
    document.querySelector('select[name="college"]').value = "{{ tenant.college }}";
    document.querySelector('select[name="branch"]').value = "{{ tenant.branch }}";
    document.querySelector('select[name="study_year"]').value = "{{ tenant.study_year }}";
});
</script>
"""
if "document.querySelector('select" not in content:
    content += js_append
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)
print("Added select script back")
