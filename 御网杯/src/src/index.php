<?php
session_start();
if (!isset($_SESSION['user_id'])) {
    $_SESSION['user_id'] = bin2hex(random_bytes(8));
    $_SESSION['balance'] = 20; // Default 20 金币
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>极简支付 - 现代数字资产商城</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f8fafc; color: #1e293b; }
        .glass-header { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(0,0,0,0.05); }
        .item-card { transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); background: #ffffff; }
        .item-card:hover { transform: translateY(-8px); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08); border-color: #cbd5e1; }
        .gradient-bg { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
        .btn-modern { transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
        .btn-modern:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
        .btn-modern:active { transform: translateY(0px); }
    </style>
</head>
<body class="antialiased min-h-screen flex flex-col">

    <header class="glass-header sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3 text-emerald-600">
                <i class="fas fa-shopping-bag text-3xl"></i>
                <span class="text-3xl font-black tracking-tight" style="font-family: 'Outfit', sans-serif;">极简支付</span>
            </div>
            <div class="flex items-center space-x-6">
                <div class="hidden sm:flex items-center bg-gray-100 rounded-full px-2 py-1 border border-gray-200 focus-within:ring-2 focus-within:ring-emerald-400 focus-within:border-transparent transition-all">
                    <input type="text" id="couponInput" placeholder="输入 Base64 代金券" class="bg-transparent border-none focus:outline-none px-4 py-1 text-sm w-48 text-gray-700">
                    <button id="applyCouponBtn" onclick="applyCoupon()" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-full transition-colors"><i class="fas fa-gift mr-1"></i> 应用</button>
                </div>

                <div class="bg-emerald-50 text-emerald-800 px-5 py-2.5 rounded-full font-bold shadow-sm flex items-center border border-emerald-100">
                    <i class="fas fa-金币 mr-2 text-yellow-500 text-lg"></i>
                    <span id="balanceDisplay" class="text-lg"><?php echo $_SESSION['balance']; ?></span> &nbsp;金币
                </div>
                <div class="text-sm text-gray-400 font-mono font-semibold">用户: <?php echo substr($_SESSION['user_id'], 0, 8); ?></div>
            </div>
        </div>
    </header>

    <main class="flex-grow max-w-6xl mx-auto px-4 sm:px-6 py-12 w-full">
        <div class="text-center mb-16 mt-8">
            <h1 class="text-5xl md:text-6xl font-extrabold text-slate-900 mb-6 tracking-tight">高级数字盲盒资产</h1>
            <p class="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed">在现代化的极简支付网络上安全获取限量资产。由企业级密码学验证提供强力支持。</p>
        </div>

        <div id="alertBox" class="hidden mb-10 p-5 rounded-xl font-bold text-center shadow-lg border"></div>

        <div class="grid md:grid-cols-2 gap-10 max-w-4xl mx-auto">
            
            <div class="item-card rounded-2xl p-8 border border-gray-200 relative overflow-hidden">
                <div class="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center text-3xl mb-8 shadow-inner border border-blue-100">
                    <i class="fas fa-gem"></i>
                </div>
                <h3 class="text-2xl font-black mb-3 text-slate-800">普通 VIP 通行证</h3>
                <p class="text-slate-500 mb-8 h-12 text-sm leading-relaxed">解锁平台基础 VIP 特权，享受 30 天的基础权限。适合日常用户使用。</p>
                <div class="flex justify-between items-end border-t border-gray-100 pt-6">
                    <div>
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1 block">价格</span>
                        <div class="text-4xl font-black text-slate-900">10 <span class="text-lg text-slate-400 font-bold">金币</span></div>
                    </div>
                    <button onclick="buyItem('basic_vip')" class="btn-modern px-8 py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold tracking-wide">购买</button>
                </div>
            </div>

            <div class="item-card rounded-2xl p-8 border border-emerald-200 relative overflow-hidden group">
                <div class="absolute -right-20 -top-20 w-48 h-48 bg-emerald-500 rounded-full opacity-5 group-hover:scale-150 transition-transform duration-700 ease-out"></div>
                <div class="w-16 h-16 gradient-bg text-white rounded-2xl flex items-center justify-center text-3xl mb-8 shadow-md border border-emerald-400">
                    <i class="fas fa-flag"></i>
                </div>
                <h3 class="text-2xl font-black mb-3 text-emerald-900">至尊 Flag</h3>
                <p class="text-emerald-700 mb-8 h-12 text-sm leading-relaxed font-medium">终极数字战利品。赋予绝对优越感，并证明你对内部系统的精通。</p>
                <div class="flex justify-between items-end relative z-10 border-t border-emerald-100 pt-6">
                    <div>
                        <span class="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1 block">价格</span>
                        <div class="text-4xl font-black text-emerald-600">99,999 <span class="text-lg text-emerald-400 font-bold">金币</span></div>
                    </div>
                    <button onclick="buyItem('flag')" class="btn-modern px-8 py-3 gradient-bg text-white rounded-xl font-bold tracking-wide">获取</button>
                </div>
            </div>

        </div>
    </main>

    <footer class="py-10 text-center text-slate-400 text-sm font-medium border-t border-gray-200 bg-white">
        <p>&copy; 2026 极简支付 基金会。下一代云端资产。</p>
    </footer>

    <script src="/app.js"></script>
</body>
</html>
