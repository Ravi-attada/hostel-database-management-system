import re

new_script = r"""<script>
let advanceTotal = 10000;

async function updateRentPreview() {
    const foodDate = document.getElementById('foodStartDate').value;
    const roomId = document.getElementById('roomId').value;
    if (!foodDate || !roomId) return;

    try {
        const res  = await fetch('/api/rent-preview?food_date=' + foodDate + '&room_id=' + encodeURIComponent(roomId));
        const data = await res.json();
        if (data.error) return;

        const html = `
          <div class="space-y-6">
            <div class="bg-sky-50 dark:bg-sky-900/20 p-4 rounded-xl border border-sky-100 dark:border-sky-800">
              <div class="font-bold text-sky-800 dark:text-sky-300 mb-1">${data.breakdown.month_name} - First Month Bill</div>
              <div class="text-sm text-sky-600 dark:text-sky-400">
                Charged for <strong>${data.breakdown.days_charged}</strong> out of <strong>${data.breakdown.days_in_month}</strong> days.
              </div>
              <div class="text-4xl font-black text-sky-600 dark:text-sky-400 mt-4">
                &#8377;${data.breakdown.total_prorated.toLocaleString('en-IN')}
              </div>
              <div class="text-xs text-sky-500 mt-2 font-medium">From next month: &#8377;${data.breakdown.full_rent}/month</div>
            </div>

            <div class="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700/50">
              <table class="w-full text-left text-sm">
                <thead class="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  <tr>
                    <th class="px-4 py-3 font-semibold">Component</th>
                    <th class="px-4 py-3 font-semibold">Full</th>
                    <th class="px-4 py-3 font-semibold">Prorated</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50 bg-white/50 dark:bg-slate-900/50">
                  <tr>
                    <td class="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">Room</td>
                    <td class="px-4 py-3 text-slate-600 dark:text-slate-400">&#8377;${data.breakdown.room_rent}</td>
                    <td class="px-4 py-3 font-bold text-slate-800 dark:text-slate-200">&#8377;${data.breakdown.prorated_room}</td>
                  </tr>
                  <tr>
                    <td class="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">Food</td>
                    <td class="px-4 py-3 text-slate-600 dark:text-slate-400">&#8377;${data.breakdown.food_rent}</td>
                    <td class="px-4 py-3 font-bold text-slate-800 dark:text-slate-200">&#8377;${data.breakdown.prorated_food}</td>
                  </tr>
                  <tr class="bg-slate-50/80 dark:bg-slate-800/80">
                    <td class="px-4 py-3 font-bold text-slate-800 dark:text-white">Total</td>
                    <td class="px-4 py-3 font-bold text-slate-800 dark:text-white">&#8377;${data.breakdown.full_rent}</td>
                    <td class="px-4 py-3 font-black text-blue-600 dark:text-blue-400">&#8377;${data.breakdown.total_prorated}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        `;
        document.getElementById('rentBreakdown').innerHTML = html;

        advanceTotal = 10000;
        document.getElementById('advanceTotalDisplay').textContent = (10000).toLocaleString('en-IN');
        calcRemaining();

    } catch(e) { console.error(e); }
}

function calcRemaining() {
    const paid = parseFloat(document.getElementById('advancePaid').value) || 0;
    const rem  = advanceTotal - paid;
    const el   = document.getElementById('advanceRemaining');
    el.innerHTML = '&#8377;' + rem.toLocaleString('en-IN');
    if (rem <= 0) {
      el.className = 'px-4 py-3 rounded-xl font-black text-xl border bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 border-emerald-200 dark:border-emerald-800';
    } else {
      el.className = 'px-4 py-3 rounded-xl font-black text-xl border bg-rose-50 dark:bg-rose-900/20 text-rose-600 border-rose-200 dark:border-rose-800';
    }
}

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => lucide.createIcons(), 100);
  updateRentPreview();
});
</script>"""

for file in ['templates/add_tenant.html', 'templates/edit_tenant.html']:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'<script>.*?</script>', new_script, content, flags=re.DOTALL)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done fixing JS!")
