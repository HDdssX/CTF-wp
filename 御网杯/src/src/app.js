/**
 * 极简支付 Frontend Logic
 * Version 1.0.4
 */

function checkHealth() {
    fetch('/api/status.php')
      .then(r => r.json())
      .then(d => {
          if(d.status !== 'online') console.warn('支付 API 离线！');
      }).catch(e => console.error(e));
}

function buyItem(item) {
    const btn = event.currentTarget || document.activeElement;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
    btn.disabled = true;

    const formData = new URLSearchParams();
    formData.append('item', item);

    fetch('/buy.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData.toString()
    })
    .then(response => response.json())
    .then(data => {
        const alertBox = document.getElementById('alertBox');
        alertBox.classList.remove('hidden', 'bg-red-100', 'text-red-800', 'bg-green-100', 'text-green-800');
        
        if (data.error) {
            alertBox.classList.add('bg-red-100', 'text-red-800');
            alertBox.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i> ${data.error}`;
        } else if (data.success) {
            alertBox.classList.add('bg-green-100', 'text-green-800');
            alertBox.innerHTML = `<i class="fas fa-check-circle mr-2"></i> ${data.message}`;
            if (data.balance !== undefined) {
                document.getElementById('balanceDisplay').innerText = data.balance;
            }
        }
        
        alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    })
    .catch(error => {
        alert('发生网络错误。');
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

function applyCoupon() {
    const btn = document.getElementById('applyCouponBtn');
    const input = document.getElementById('couponInput');
    const originalText = btn.innerHTML;
    const b64 = input.value.trim();
    if (!b64) return;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在应用';
    btn.disabled = true;

    const fp = new URLSearchParams();
    fp.append('coupon', b64);

    fetch('/api/apply_coupon.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: fp.toString()
    })
    .then(r => r.json())
    .then(data => {
        if(data.error) alert(data.error);
        else {
            alert('代金券应用成功！余额已更新。');
            location.reload(); // reload to reflect the balance
        }
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        input.value = "";
    });
}

window.onload = checkHealth;
