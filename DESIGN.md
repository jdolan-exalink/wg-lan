<!-- Login -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=Space+Grotesk:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
              "surface-container-low": "#191838",
              "surface-container-highest": "#333152",
              "on-background": "#e3dfff",
              "surface-dim": "#110f2f",
              "tertiary-fixed-dim": "#00daf3",
              "surface-tint": "#c7bfff",
              "surface": "#110f2f",
              "surface-container": "#1d1c3c",
              "primary-fixed-dim": "#c7bfff",
              "on-tertiary-container": "#b8f4ff",
              "on-tertiary-fixed": "#001f24",
              "on-primary-fixed-variant": "#3e15d2",
              "primary": "#c7bfff",
              "surface-container-lowest": "#0c092a",
              "outline": "#928ea1",
              "on-primary-fixed": "#170065",
              "surface-bright": "#373557",
              "tertiary-fixed": "#9cf0ff",
              "on-surface-variant": "#c8c4d8",
              "outline-variant": "#474555",
              "primary-container": "#624af4",
              "inverse-on-surface": "#2e2d4e",
              "on-secondary": "#2e2e49",
              "secondary": "#c5c3e5",
              "primary-fixed": "#e4dfff",
              "background": "#110f2f",
              "secondary-fixed": "#e2dfff",
              "tertiary": "#00daf3",
              "tertiary-container": "#007482",
              "on-secondary-fixed-variant": "#444460",
              "error-container": "#93000a",
              "surface-container-high": "#282647",
              "on-tertiary-fixed-variant": "#004f58",
              "on-primary-container": "#ebe6ff",
              "on-primary": "#29009f",
              "on-tertiary": "#00363d",
              "surface-variant": "#333152",
              "secondary-fixed-dim": "#c5c3e5",
              "inverse-primary": "#573de9",
              "secondary-container": "#474663",
              "on-error-container": "#ffdad6",
              "inverse-surface": "#e3dfff",
              "on-secondary-fixed": "#191933",
              "on-secondary-container": "#b7b5d7",
              "on-error": "#690005",
              "on-surface": "#e3dfff",
              "error": "#ffb4ab"
            },
            fontFamily: {
              "headline": ["Inter"],
              "body": ["Inter"],
              "label": ["Space Grotesk"]
            },
            borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
          },
        },
      }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            display: inline-block;
            line-height: 1;
            text-transform: none;
            letter-spacing: normal;
            word-wrap: normal;
            white-space: nowrap;
            direction: ltr;
        }
        .kinetic-glow {
            box-shadow: 0 0 40px -10px rgba(98, 74, 244, 0.3);
        }
        .glass-panel {
            background: linear-gradient(135deg, rgba(29, 28, 60, 0.8) 0%, rgba(17, 15, 47, 0.9) 100%);
            backdrop-filter: blur(20px);
        }
        .inner-glow {
            box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="bg-surface text-on-surface font-body min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
<!-- Background Decoration -->
<div class="absolute inset-0 z-0 pointer-events-none">
<div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary-container opacity-[0.03] blur-[120px]"></div>
<div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-tertiary opacity-[0.02] blur-[150px]"></div>
<div class="absolute inset-0" data-alt="Subtle grid pattern of tiny dark dots on a deep obsidian background for a technical texture" style="background-image: radial-gradient(circle at 2px 2px, rgba(71, 69, 85, 0.05) 1px, transparent 0); background-size: 40px 40px;"></div>
</div>
<!-- Main Login Portal -->
<main class="z-10 w-full max-w-md px-6">
<!-- Logo Header -->
<div class="text-center mb-10">
<div class="inline-flex items-center justify-center mb-4">
<span class="material-symbols-outlined text-primary-container text-5xl" style="font-variation-settings: 'FILL' 1;">hub</span>
</div>
<h1 class="font-headline font-black text-4xl tracking-tighter text-on-surface">
                NetLoom
            </h1>
<p class="font-label text-xs uppercase tracking-widest text-outline mt-2">
                Network Orchestrator • v2.4.0
            </p>
</div>
<!-- Central Login Card -->
<div class="glass-panel kinetic-glow border border-outline-variant/15 rounded-xl p-8 relative overflow-hidden">
<!-- Subtle top highlight line -->
<div class="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent"></div>
<form action="#" class="space-y-6">
<!-- Username Field -->
<div class="space-y-2">
<label class="font-label text-[10px] uppercase tracking-widest text-outline-variant block ml-1" for="username">
                        System Identity
                    </label>
<div class="relative group">
<div class="absolute inset-y-0 left-4 flex items-center pointer-events-none text-outline-variant group-focus-within:text-primary transition-colors">
<span class="material-symbols-outlined text-xl">account_circle</span>
</div>
<input class="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg py-3.5 pl-12 pr-4 text-sm font-body text-on-surface placeholder:text-outline-variant focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-all duration-200" id="username" placeholder="Username" type="text"/>
</div>
</div>
<!-- Password Field -->
<div class="space-y-2">
<div class="flex justify-between items-center px-1">
<label class="font-label text-[10px] uppercase tracking-widest text-outline-variant block" for="password">
                            Security Key
                        </label>
<a class="font-label text-[10px] uppercase tracking-widest text-primary-container hover:text-primary transition-colors" href="#">
                            Forgot?
                        </a>
</div>
<div class="relative group">
<div class="absolute inset-y-0 left-4 flex items-center pointer-events-none text-outline-variant group-focus-within:text-primary transition-colors">
<span class="material-symbols-outlined text-xl">lock</span>
</div>
<input class="w-full bg-surface-container-lowest border border-outline-variant/15 rounded-lg py-3.5 pl-12 pr-4 text-sm font-body text-on-surface placeholder:text-outline-variant focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-all duration-200" id="password" placeholder="••••••••" type="password"/>
<div class="absolute inset-y-0 right-4 flex items-center cursor-pointer text-outline-variant hover:text-on-surface">
<span class="material-symbols-outlined text-xl">visibility</span>
</div>
</div>
</div>
<!-- Sign In Button -->
<button class="w-full py-4 px-6 rounded-lg bg-primary-container text-on-primary-container font-headline font-bold text-sm tracking-tight transition-all duration-200 hover:scale-[1.01] active:scale-[0.98] inner-glow flex items-center justify-center gap-2 group" type="submit">
                    Sign In to Portal
                    <span class="material-symbols-outlined text-xl transition-transform group-hover:translate-x-1">arrow_forward</span>
</button>
</form>
<!-- Bottom Action -->
<div class="mt-8 pt-6 border-t border-outline-variant/10 text-center">
<p class="text-sm text-outline font-body">
                    Unauthorized access is monitored. 
                    <a class="text-tertiary-fixed-dim font-medium hover:underline ml-1" href="#">Request Credentials</a>
</p>
</div>
</div>
<!-- Auxiliary Links -->
<div class="mt-8 flex justify-center gap-8">
<div class="flex items-center gap-2 text-outline-variant hover:text-outline transition-colors cursor-pointer">
<span class="material-symbols-outlined text-lg">shield</span>
<span class="font-label text-[10px] uppercase tracking-widest">Global Security</span>
</div>
<div class="flex items-center gap-2 text-outline-variant hover:text-outline transition-colors cursor-pointer">
<span class="material-symbols-outlined text-lg">language</span>
<span class="font-label text-[10px] uppercase tracking-widest">Network Status</span>
</div>
</div>
</main>
<!-- Minimalist Footer -->
<footer class="absolute bottom-8 w-full px-8 flex flex-col md:flex-row justify-between items-center opacity-40">
<div class="flex items-center gap-4 mb-4 md:mb-0">
<p class="font-label text-[10px] uppercase tracking-widest text-outline">
                © 2024 NetLoom Systems
            </p>
<div class="w-1 h-1 rounded-full bg-outline-variant"></div>
<p class="font-label text-[10px] uppercase tracking-widest text-outline">
                All Rights Reserved
            </p>
</div>
<div class="flex items-center gap-3">
<div class="flex items-center gap-1.5 px-2 py-1 rounded bg-surface-container-high border border-outline-variant/10">
<div class="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse shadow-[0_0_8px_rgba(0,218,243,0.6)]"></div>
<span class="font-label text-[10px] uppercase tracking-widest text-tertiary">System Online</span>
</div>
<p class="font-label text-[10px] uppercase tracking-widest text-outline">
                Build 2024.08.12
            </p>
</div>
</footer>
</body></html>

<!-- Dashboard -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&amp;family=Space+Grotesk:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
              "surface-tint": "#c7bfff",
              "on-primary": "#29009f",
              "primary": "#c7bfff",
              "surface-container-highest": "#333152",
              "surface-dim": "#110f2f",
              "on-primary-fixed": "#170065",
              "primary-fixed-dim": "#c7bfff",
              "tertiary-fixed": "#9cf0ff",
              "surface-container-lowest": "#0c092a",
              "on-tertiary-fixed-variant": "#004f58",
              "inverse-on-surface": "#2e2d4e",
              "inverse-surface": "#e3dfff",
              "primary-container": "#624af4",
              "outline-variant": "#474555",
              "on-secondary-container": "#b7b5d7",
              "secondary-fixed-dim": "#c5c3e5",
              "surface-container-low": "#191838",
              "primary-fixed": "#e4dfff",
              "tertiary-fixed-dim": "#00daf3",
              "on-tertiary": "#00363d",
              "on-surface-variant": "#c8c4d8",
              "tertiary": "#00daf3",
              "on-secondary-fixed": "#191933",
              "error-container": "#93000a",
              "tertiary-container": "#007482",
              "secondary": "#c5c3e5",
              "on-primary-container": "#ebe6ff",
              "on-secondary": "#2e2e49",
              "surface-container-high": "#282647",
              "surface": "#110f2f",
              "on-surface": "#e3dfff",
              "background": "#110f2f",
              "on-error": "#690005",
              "secondary-container": "#474663",
              "secondary-fixed": "#e2dfff",
              "on-tertiary-fixed": "#001f24",
              "outline": "#928ea1",
              "surface-container": "#1d1c3c",
              "surface-variant": "#333152",
              "on-background": "#e3dfff",
              "surface-bright": "#373557",
              "on-secondary-fixed-variant": "#444460",
              "inverse-primary": "#573de9",
              "on-tertiary-container": "#b8f4ff",
              "on-error-container": "#ffdad6",
              "error": "#ffb4ab",
              "on-primary-fixed-variant": "#3e15d2"
            },
            fontFamily: {
              "headline": ["Inter"],
              "body": ["Inter"],
              "label": ["Space Grotesk"]
            },
            borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
          },
        },
      }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .glass-card {
            background: rgba(29, 28, 60, 0.4);
            backdrop-filter: blur(12px);
            border-top: 1px solid rgba(71, 69, 85, 0.15);
        }
        .kinetic-gradient {
            background: linear-gradient(135deg, #624af4 0%, #00daf3 100%);
        }
    </style>
</head>
<body class="bg-background text-on-surface font-body selection:bg-primary-container selection:text-on-primary-container">
<!-- SideNavBar Shell -->
<aside class="fixed left-0 top-0 h-full flex flex-col py-6 bg-[#1d1c3c] dark:bg-[#1d1c3c] w-64 z-50">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tighter text-[#e3dfff] font-headline">NetLoom</h1>
<p class="font-label text-xs tracking-tight text-outline">Orchestrator v1.0</p>
</div>
<nav class="flex-1 space-y-1">
<!-- Active Navigation: Dashboard -->
<a class="bg-[#282647] text-[#00daf3] rounded-lg mx-2 my-1 transition-all duration-300 px-4 py-3 flex items-center gap-3" href="#">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">dashboard</span>
<span class="font-label text-xs tracking-tight uppercase">Dashboard</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined">hub</span>
<span class="font-label text-xs tracking-tight uppercase">Peers</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined">lan</span>
<span class="font-label text-xs tracking-tight uppercase">Networks</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined">security</span>
<span class="font-label text-xs tracking-tight uppercase">Zones</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined">group</span>
<span class="font-label text-xs tracking-tight uppercase">Groups</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined">policy</span>
<span class="font-label text-xs tracking-tight uppercase">Policies</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined">settings</span>
<span class="font-label text-xs tracking-tight uppercase">System</span>
</a>
</nav>
<div class="px-6 mt-auto">
<div class="flex items-center gap-3 p-3 rounded-xl bg-surface-container-high/40">
<div class="w-8 h-8 rounded-full overflow-hidden bg-primary-container flex items-center justify-center">
<img alt="Admin User" class="w-full h-full object-cover" data-alt="professional portrait of a system administrator avatar in a minimalist vector style with deep purple background" src="https://lh3.googleusercontent.com/aida-public/AB6AXuALsQCNCv9xoiiUyzleNxp4EiqHlfl-u8buxUUibfnRx70oki562vw_UM9aKqK8Qyr6PiZzVq1Pucf6VAjF_B61MZxAtRciPDg8plH8n0HpwyTcD4fIvPHQ5kasVVE7AoKxyuekOy9zSOG_efGZ9PL2yRaTVV7M60fyDavgT8PFPxiyK2RQv6z37ypQMcC7l6BEYswwoeZ5ZIq2lkciTbKBit_3zsDdh-2HryOYNYp7FYOhMxirScUrBGug_qCmGWH1r50OECdlTBw"/>
</div>
<div class="overflow-hidden">
<p class="text-sm font-semibold truncate">Admin User</p>
<p class="text-[10px] text-outline uppercase font-label">Root Node</p>
</div>
</div>
</div>
</aside>
<!-- TopNavBar Shell -->
<header class="flex justify-between items-center h-16 px-8 ml-64 w-[calc(100%-16rem)] bg-[#110f2f]/80 backdrop-blur-xl fixed top-0 z-40">
<div class="flex items-center gap-4">
<h2 class="font-headline font-bold text-lg tracking-tight text-on-surface">Network Overview</h2>
<div class="h-4 w-px bg-outline-variant/30"></div>
<p class="font-label text-xs text-tertiary">NODE-01-TX-DAL</p>
</div>
<div class="flex items-center gap-6">
<div class="relative group hidden lg:block">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
<input class="bg-surface-container-low border-none rounded-lg pl-10 pr-4 py-2 text-sm w-64 focus:ring-1 focus:ring-primary-container transition-all font-body" placeholder="Search Peers or Networks..." type="text"/>
</div>
<div class="flex items-center gap-4">
<button class="text-outline hover:text-on-surface transition-colors cursor-pointer active:opacity-70">
<span class="material-symbols-outlined">dark_mode</span>
</button>
<button class="text-outline hover:text-on-surface transition-colors cursor-pointer active:opacity-70 relative">
<span class="material-symbols-outlined">notifications</span>
<span class="absolute top-0 right-0 w-2 h-2 bg-error rounded-full border-2 border-surface"></span>
</button>
</div>
</div>
</header>
<!-- Main Content Canvas -->
<main class="ml-64 pt-24 pb-12 px-8 min-h-screen">
<!-- High Level Stats Bento Grid -->
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
<!-- Total Peers -->
<div class="bg-surface-container p-6 rounded-xl flex flex-col justify-between hover:bg-surface-container-high transition-colors group">
<div class="flex justify-between items-start mb-4">
<span class="font-label text-xs uppercase tracking-widest text-outline">Total Peers</span>
<div class="p-2 rounded-lg bg-primary-container/10 text-primary">
<span class="material-symbols-outlined">hub</span>
</div>
</div>
<div>
<h3 class="text-4xl font-bold font-headline mb-1">1,284</h3>
<p class="text-xs text-tertiary font-label flex items-center gap-1">
<span class="material-symbols-outlined text-xs">trending_up</span>
                        +12% from last sync
                    </p>
</div>
</div>
<!-- Online Status -->
<div class="bg-surface-container p-6 rounded-xl flex flex-col justify-between hover:bg-surface-container-high transition-colors group">
<div class="flex justify-between items-start mb-4">
<span class="font-label text-xs uppercase tracking-widest text-outline">Active Nodes</span>
<div class="p-2 rounded-lg bg-tertiary-container/10 text-tertiary">
<span class="material-symbols-outlined">online_prediction</span>
</div>
</div>
<div>
<h3 class="text-4xl font-bold font-headline mb-1">1,241</h3>
<p class="text-xs text-outline font-label flex items-center gap-1">
                        96.6% Availability
                    </p>
</div>
</div>
<!-- Offline Status -->
<div class="bg-surface-container p-6 rounded-xl flex flex-col justify-between hover:bg-surface-container-high transition-colors group">
<div class="flex justify-between items-start mb-4">
<span class="font-label text-xs uppercase tracking-widest text-outline">Offline / Alerts</span>
<div class="p-2 rounded-lg bg-error-container/10 text-error">
<span class="material-symbols-outlined">warning</span>
</div>
</div>
<div>
<h3 class="text-4xl font-bold font-headline mb-1">43</h3>
<p class="text-xs text-error font-label flex items-center gap-1">
                        Action Required
                    </p>
</div>
</div>
<!-- Traffic Stats -->
<div class="bg-surface-container p-6 rounded-xl kinetic-gradient flex flex-col justify-between shadow-2xl shadow-primary-container/20">
<div class="flex justify-between items-start mb-4">
<span class="font-label text-xs uppercase tracking-widest text-on-primary-container">Total Traffic (24h)</span>
<div class="p-2 rounded-lg bg-white/10 text-white">
<span class="material-symbols-outlined">speed</span>
</div>
</div>
<div class="text-on-primary-container">
<h3 class="text-4xl font-bold font-headline mb-1">8.42 TB</h3>
<p class="text-xs font-label flex items-center gap-1 opacity-80">
                        Peak: 450 Gbps
                    </p>
</div>
</div>
</div>
<!-- Charts and Detailed Analytics -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
<div class="lg:col-span-2 bg-surface-container-low rounded-xl p-8">
<div class="flex justify-between items-center mb-10">
<div>
<h4 class="font-headline font-bold text-lg">Top Peers by Traffic</h4>
<p class="text-sm text-outline">Throughput distribution across top 5 regional nodes</p>
</div>
<button class="bg-surface-container-high px-4 py-2 rounded-lg text-xs font-label uppercase tracking-wider hover:bg-surface-bright transition-colors">
                        Detailed Logs
                    </button>
</div>
<!-- Traffic Visualization (Placeholder) -->
<div class="h-64 flex items-end justify-between gap-4 px-4">
<div class="w-full flex flex-col items-center gap-4">
<div class="w-full kinetic-gradient rounded-t-lg opacity-40 hover:opacity-100 transition-opacity" style="height: 60%;"></div>
<span class="font-label text-[10px] text-outline uppercase">NYC-ED-01</span>
</div>
<div class="w-full flex flex-col items-center gap-4">
<div class="w-full kinetic-gradient rounded-t-lg opacity-60 hover:opacity-100 transition-opacity" style="height: 85%;"></div>
<span class="font-label text-[10px] text-outline uppercase">LDN-UK-04</span>
</div>
<div class="w-full flex flex-col items-center gap-4">
<div class="w-full kinetic-gradient rounded-t-lg opacity-100 hover:opacity-100 transition-opacity" style="height: 100%;"></div>
<span class="font-label text-[10px] text-outline uppercase">TKY-JP-12</span>
</div>
<div class="w-full flex flex-col items-center gap-4">
<div class="w-full kinetic-gradient rounded-t-lg opacity-30 hover:opacity-100 transition-opacity" style="height: 45%;"></div>
<span class="font-label text-[10px] text-outline uppercase">FRA-DE-02</span>
</div>
<div class="w-full flex flex-col items-center gap-4">
<div class="w-full kinetic-gradient rounded-t-lg opacity-50 hover:opacity-100 transition-opacity" style="height: 70%;"></div>
<span class="font-label text-[10px] text-outline uppercase">SGP-SG-09</span>
</div>
</div>
</div>
<!-- Health Snapshot Card -->
<div class="bg-surface-container-low rounded-xl p-8 relative overflow-hidden group">
<div class="absolute -right-12 -top-12 w-48 h-48 bg-primary/5 rounded-full blur-3xl"></div>
<h4 class="font-headline font-bold text-lg mb-6">Global Health</h4>
<div class="space-y-6">
<div>
<div class="flex justify-between text-xs font-label uppercase mb-2">
<span class="text-outline">Latency (Avg)</span>
<span class="text-tertiary">24ms</span>
</div>
<div class="h-1 bg-surface-container-highest rounded-full">
<div class="h-full bg-tertiary rounded-full" style="width: 88%"></div>
</div>
</div>
<div>
<div class="flex justify-between text-xs font-label uppercase mb-2">
<span class="text-outline">Packet Loss</span>
<span class="text-primary">0.002%</span>
</div>
<div class="h-1 bg-surface-container-highest rounded-full">
<div class="h-full bg-primary rounded-full" style="width: 98%"></div>
</div>
</div>
<div>
<div class="flex justify-between text-xs font-label uppercase mb-2">
<span class="text-outline">Encrypted Tunneling</span>
<span class="text-on-surface">100% Secure</span>
</div>
<div class="h-1 bg-surface-container-highest rounded-full">
<div class="h-full bg-on-surface rounded-full" style="width: 100%"></div>
</div>
</div>
</div>
<div class="mt-10 p-4 glass-card rounded-xl">
<p class="text-xs text-outline mb-3 font-label">LAST ORCHESTRATION EVENT</p>
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-tertiary">check_circle</span>
<p class="text-sm font-medium">Re-routed 4 peers to US-EAST-1 via secondary uplink.</p>
</div>
<p class="text-[10px] text-outline mt-2 font-label">2 MINUTES AGO</p>
</div>
</div>
</div>
<!-- Peer Status Table -->
<section class="bg-surface-container rounded-xl overflow-hidden">
<div class="p-6 flex justify-between items-center">
<h4 class="font-headline font-bold text-lg">Active Peer List</h4>
<div class="flex items-center gap-2">
<span class="font-label text-xs text-outline">Filter:</span>
<select class="bg-surface-container-low border-none rounded-lg text-xs font-label py-1 focus:ring-0">
<option>All Status</option>
<option>Online Only</option>
<option>Alerting</option>
</select>
</div>
</div>
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low">
<tr class="font-label text-[10px] uppercase tracking-widest text-outline">
<th class="px-6 py-4">Name</th>
<th class="px-6 py-4">Type</th>
<th class="px-6 py-4">IP Address</th>
<th class="px-6 py-4">Status</th>
<th class="px-6 py-4">Handshake</th>
<th class="px-6 py-4 text-right">RX / TX</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/10">
<tr class="hover:bg-surface-container-high transition-colors group">
<td class="px-6 py-4">
<div class="flex items-center gap-3">
<div class="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
<span class="material-symbols-outlined text-sm">laptop_mac</span>
</div>
<span class="font-semibold text-sm">MBP-ALICE-LOCAL</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs">Workstation</td>
<td class="px-6 py-4 font-label text-xs text-primary">10.8.0.124</td>
<td class="px-6 py-4">
<div class="inline-flex items-center gap-2 px-2 py-1 rounded bg-tertiary-container/10 border border-tertiary/10">
<span class="w-1.5 h-1.5 rounded-full bg-tertiary shadow-[0_0_8px_rgba(0,218,243,0.6)]"></span>
<span class="text-[10px] font-label font-bold text-tertiary uppercase">Online</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs text-outline">24s ago</td>
<td class="px-6 py-4 text-right font-label text-xs">
<span class="text-tertiary">421 MB</span> / <span class="text-outline">12 GB</span>
</td>
</tr>
<tr class="hover:bg-surface-container-high transition-colors group">
<td class="px-6 py-4">
<div class="flex items-center gap-3">
<div class="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
<span class="material-symbols-outlined text-sm">dns</span>
</div>
<span class="font-semibold text-sm">AWS-PROD-RELAY</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs">Cloud Gateway</td>
<td class="px-6 py-4 font-label text-xs text-primary">44.204.1.12</td>
<td class="px-6 py-4">
<div class="inline-flex items-center gap-2 px-2 py-1 rounded bg-tertiary-container/10 border border-tertiary/10">
<span class="w-1.5 h-1.5 rounded-full bg-tertiary shadow-[0_0_8px_rgba(0,218,243,0.6)]"></span>
<span class="text-[10px] font-label font-bold text-tertiary uppercase">Online</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs text-outline">1s ago</td>
<td class="px-6 py-4 text-right font-label text-xs">
<span class="text-tertiary">1.2 TB</span> / <span class="text-outline">842 GB</span>
</td>
</tr>
<tr class="hover:bg-surface-container-high transition-colors group">
<td class="px-6 py-4">
<div class="flex items-center gap-3">
<div class="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
<span class="material-symbols-outlined text-sm">router</span>
</div>
<span class="font-semibold text-sm">BRANCH-OFFICE-RTR</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs">Edge Router</td>
<td class="px-6 py-4 font-label text-xs text-primary">192.168.4.1</td>
<td class="px-6 py-4">
<div class="inline-flex items-center gap-2 px-2 py-1 rounded bg-error-container/10 border border-error/10">
<span class="w-1.5 h-1.5 rounded-full bg-error"></span>
<span class="text-[10px] font-label font-bold text-error uppercase">Offline</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs text-outline">4h ago</td>
<td class="px-6 py-4 text-right font-label text-xs">
<span class="text-tertiary">0 B</span> / <span class="text-outline">0 B</span>
</td>
</tr>
<tr class="hover:bg-surface-container-high transition-colors group">
<td class="px-6 py-4">
<div class="flex items-center gap-3">
<div class="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
<span class="material-symbols-outlined text-sm">smartphone</span>
</div>
<span class="font-semibold text-sm">IPHONE-BOB-ROAM</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs">Mobile</td>
<td class="px-6 py-4 font-label text-xs text-primary">10.8.0.22</td>
<td class="px-6 py-4">
<div class="inline-flex items-center gap-2 px-2 py-1 rounded bg-tertiary-container/10 border border-tertiary/10">
<span class="w-1.5 h-1.5 rounded-full bg-tertiary shadow-[0_0_8px_rgba(0,218,243,0.6)]"></span>
<span class="text-[10px] font-label font-bold text-tertiary uppercase">Online</span>
</div>
</td>
<td class="px-6 py-4 font-label text-xs text-outline">2m ago</td>
<td class="px-6 py-4 text-right font-label text-xs">
<span class="text-tertiary">84 MB</span> / <span class="text-outline">14 MB</span>
</td>
</tr>
</tbody>
</table>
</div>
<div class="p-6 bg-surface-container-low flex justify-center">
<button class="text-primary font-label text-xs tracking-widest uppercase flex items-center gap-2 hover:opacity-70 transition-opacity">
                    Load More Peers
                    <span class="material-symbols-outlined text-sm">keyboard_arrow_down</span>
</button>
</div>
</section>
</main>
<!-- BottomNavBar Shell -->
<footer class="fixed bottom-0 right-0 w-[calc(100%-16rem)] h-8 bg-[#110f2f] flex justify-end gap-6 px-8 items-center z-50 border-t border-[#474555]/15">
<div class="flex items-center gap-2 text-[#00daf3] animate-pulse">
<span class="material-symbols-outlined text-xs">database</span>
<span class="font-label font-medium text-[10px] uppercase tracking-widest">DB: Connected</span>
</div>
<div class="flex items-center gap-2 text-[#928ea1] opacity-60">
<span class="material-symbols-outlined text-xs">vpn_lock</span>
<span class="font-label font-medium text-[10px] uppercase tracking-widest">WG: Active</span>
</div>
</footer>
</body></html>

<!-- Networks -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&amp;family=Space+Grotesk:wght@400;500;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
              "surface-tint": "#c7bfff",
              "on-primary": "#29009f",
              "primary": "#c7bfff",
              "surface-container-highest": "#333152",
              "surface-dim": "#110f2f",
              "on-primary-fixed": "#170065",
              "primary-fixed-dim": "#c7bfff",
              "tertiary-fixed": "#9cf0ff",
              "surface-container-lowest": "#0c092a",
              "on-tertiary-fixed-variant": "#004f58",
              "inverse-on-surface": "#2e2d4e",
              "inverse-surface": "#e3dfff",
              "primary-container": "#624af4",
              "outline-variant": "#474555",
              "on-secondary-container": "#b7b5d7",
              "secondary-fixed-dim": "#c5c3e5",
              "surface-container-low": "#191838",
              "primary-fixed": "#e4dfff",
              "tertiary-fixed-dim": "#00daf3",
              "on-tertiary": "#00363d",
              "on-surface-variant": "#c8c4d8",
              "tertiary": "#00daf3",
              "on-secondary-fixed": "#191933",
              "error-container": "#93000a",
              "tertiary-container": "#007482",
              "secondary": "#c5c3e5",
              "on-primary-container": "#ebe6ff",
              "on-secondary": "#2e2e49",
              "surface-container-high": "#282647",
              "surface": "#110f2f",
              "on-surface": "#e3dfff",
              "background": "#110f2f",
              "on-error": "#690005",
              "secondary-container": "#474663",
              "secondary-fixed": "#e2dfff",
              "on-tertiary-fixed": "#001f24",
              "outline": "#928ea1",
              "surface-container": "#1d1c3c",
              "surface-variant": "#333152",
              "on-background": "#e3dfff",
              "surface-bright": "#373557",
              "on-secondary-fixed-variant": "#444460",
              "inverse-primary": "#573de9",
              "on-tertiary-container": "#b8f4ff",
              "on-error-container": "#ffdad6",
              "error": "#ffb4ab",
              "on-primary-fixed-variant": "#3e15d2"
            },
            fontFamily: {
              "headline": ["Inter"],
              "body": ["Inter"],
              "label": ["Space Grotesk"]
            },
            borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
          },
        },
      }
    </script>
<style>
        body {
            background-color: #110f2f;
            color: #e3dfff;
            font-family: 'Inter', sans-serif;
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .kinetic-gradient {
            background: linear-gradient(135deg, #624af4 0%, #00daf3 100%);
        }
        .glass-panel {
            background: rgba(51, 49, 82, 0.6);
            backdrop-filter: blur(20px);
        }
        .no-scrollbar::-webkit-scrollbar {
            display: none;
        }
    </style>
</head>
<body class="bg-surface text-on-surface min-h-screen selection:bg-primary-container selection:text-on-primary-container">
<!-- SideNavBar Shell -->
<aside class="fixed left-0 top-0 h-full flex flex-col py-6 bg-[#1d1c3c] dark:bg-[#1d1c3c] w-64 z-50">
<div class="px-6 mb-10">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg kinetic-gradient flex items-center justify-center shadow-lg shadow-primary-container/20">
<span class="material-symbols-outlined text-on-primary-container" style="font-variation-settings: 'FILL' 1;">hub</span>
</div>
<div>
<h1 class="text-xl font-bold tracking-tighter text-[#e3dfff] font-headline">NetLoom</h1>
<p class="font-label text-[10px] uppercase tracking-widest text-outline">Orchestrator v1.0</p>
</div>
</div>
</div>
<nav class="flex-1 space-y-1 px-2">
<!-- Dashboard -->
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-all duration-300 rounded-lg group" href="#">
<span class="material-symbols-outlined group-hover:text-primary">dashboard</span>
<span class="font-label text-xs tracking-tight">Dashboard</span>
</a>
<!-- Peers -->
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-all duration-300 rounded-lg group" href="#">
<span class="material-symbols-outlined group-hover:text-primary">hub</span>
<span class="font-label text-xs tracking-tight">Peers</span>
</a>
<!-- Networks (ACTIVE) -->
<a class="bg-[#282647] text-[#00daf3] rounded-lg mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-all duration-300 shadow-sm shadow-black/20" href="#">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">lan</span>
<span class="font-label text-xs tracking-tight font-semibold">Networks</span>
</a>
<!-- Zones -->
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-all duration-300 rounded-lg group" href="#">
<span class="material-symbols-outlined group-hover:text-primary">security</span>
<span class="font-label text-xs tracking-tight">Zones</span>
</a>
<!-- Groups -->
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-all duration-300 rounded-lg group" href="#">
<span class="material-symbols-outlined group-hover:text-primary">group</span>
<span class="font-label text-xs tracking-tight">Groups</span>
</a>
<!-- Policies -->
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-all duration-300 rounded-lg group" href="#">
<span class="material-symbols-outlined group-hover:text-primary">policy</span>
<span class="font-label text-xs tracking-tight">Policies</span>
</a>
<!-- System -->
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-all duration-300 rounded-lg group" href="#">
<span class="material-symbols-outlined group-hover:text-primary">settings</span>
<span class="font-label text-xs tracking-tight">System</span>
</a>
</nav>
<div class="px-6 pt-6 mt-auto border-t border-outline-variant/10">
<div class="flex items-center gap-3 p-2 rounded-xl bg-surface-container-low/50">
<div class="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center text-[10px] font-bold text-on-secondary-container">
                    AU
                </div>
<div class="flex-1 overflow-hidden">
<p class="text-xs font-semibold truncate">Admin User</p>
<p class="text-[10px] text-outline truncate font-label">root@netloom.io</p>
</div>
<span class="material-symbols-outlined text-outline text-sm">unfold_more</span>
</div>
</div>
</aside>
<!-- Main Canvas -->
<main class="ml-64 min-h-screen flex flex-col pb-8">
<!-- TopNavBar Shell -->
<header class="sticky top-0 z-40 flex justify-between items-center h-16 px-8 bg-[#110f2f]/80 backdrop-blur-xl transition-all duration-300">
<div class="flex items-center gap-4">
<h2 class="font-headline font-bold text-lg text-on-surface">Networks</h2>
<div class="h-4 w-[1px] bg-outline-variant/30"></div>
<nav class="flex gap-6">
<a class="text-[#c7bfff] border-b-2 border-[#624af4] h-16 flex items-center font-label text-sm px-1" href="#">Subnets</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] h-16 flex items-center font-label text-sm transition-opacity px-1" href="#">Routes</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] h-16 flex items-center font-label text-sm transition-opacity px-1" href="#">DNS</a>
</nav>
</div>
<div class="flex items-center gap-6">
<div class="relative group">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
<input class="bg-surface-container-low border-none rounded-lg pl-10 pr-4 py-1.5 text-sm font-label focus:ring-1 focus:ring-primary w-64 transition-all duration-300 placeholder:text-outline/50" placeholder="Search subnets..." type="text"/>
</div>
<div class="flex items-center gap-2">
<button class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-surface-container-high transition-colors text-outline hover:text-primary">
<span class="material-symbols-outlined">dark_mode</span>
</button>
<button class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-surface-container-high transition-colors text-outline hover:text-primary relative">
<span class="material-symbols-outlined">notifications</span>
<span class="absolute top-2.5 right-2.5 w-2 h-2 bg-error rounded-full border-2 border-surface"></span>
</button>
</div>
</div>
</header>
<!-- Content Canvas -->
<div class="px-10 pt-10 flex-1">
<!-- Page Header Area -->
<div class="flex justify-between items-end mb-12">
<div class="max-w-2xl">
<h3 class="font-headline text-3xl font-extrabold tracking-tight mb-2">VPN Tunnel Subnets</h3>
<p class="text-outline font-body leading-relaxed">
                        Define and manage the virtual address spaces assigned to your peers. These networks facilitate secure, encrypted communication across your decentralized fabric.
                    </p>
</div>
<button class="kinetic-gradient text-on-primary-container px-6 py-3 rounded-lg font-bold flex items-center gap-2 shadow-xl shadow-primary-container/20 hover:scale-[1.02] active:scale-95 transition-all group">
<span class="material-symbols-outlined text-xl group-hover:rotate-90 transition-transform duration-300">add</span>
<span class="font-label tracking-tight uppercase text-xs">Add Network</span>
</button>
</div>
<!-- Bento Grid / Table Layout -->
<div class="space-y-6">
<!-- Metrics Bar (Contextual) -->
<div class="grid grid-cols-4 gap-6">
<div class="bg-surface-container-low rounded-xl p-6 border-t border-outline-variant/15 flex items-center gap-4">
<div class="w-12 h-12 rounded-full bg-primary-container/10 flex items-center justify-center text-primary">
<span class="material-symbols-outlined">lan</span>
</div>
<div>
<p class="text-[10px] uppercase font-label tracking-widest text-outline mb-1">Active Nets</p>
<p class="text-2xl font-bold font-headline">0</p>
</div>
</div>
<div class="bg-surface-container-low rounded-xl p-6 border-t border-outline-variant/15 flex items-center gap-4">
<div class="w-12 h-12 rounded-full bg-tertiary-container/10 flex items-center justify-center text-tertiary">
<span class="material-symbols-outlined">router</span>
</div>
<div>
<p class="text-[10px] uppercase font-label tracking-widest text-outline mb-1">Allocated IPs</p>
<p class="text-2xl font-bold font-headline">0</p>
</div>
</div>
<div class="bg-surface-container-low rounded-xl p-6 border-t border-outline-variant/15 flex items-center gap-4">
<div class="w-12 h-12 rounded-full bg-secondary-container/10 flex items-center justify-center text-secondary">
<span class="material-symbols-outlined">security</span>
</div>
<div>
<p class="text-[10px] uppercase font-label tracking-widest text-outline mb-1">Isolation</p>
<p class="text-2xl font-bold font-headline">Enabled</p>
</div>
</div>
<div class="bg-surface-container-low rounded-xl p-6 border-t border-outline-variant/15 flex items-center gap-4">
<div class="w-12 h-12 rounded-full bg-surface-container-highest flex items-center justify-center text-outline">
<span class="material-symbols-outlined">sync</span>
</div>
<div>
<p class="text-[10px] uppercase font-label tracking-widest text-outline mb-1">Last Sync</p>
<p class="text-sm font-bold font-headline">Just now</p>
</div>
</div>
</div>
<!-- Main Data Container -->
<div class="bg-surface-container rounded-xl overflow-hidden border border-outline-variant/10 shadow-2xl">
<div class="bg-surface-container-low px-8 py-4 flex justify-between items-center">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-outline">list</span>
<span class="font-label text-sm font-medium tracking-tight">Configured Subnets</span>
</div>
<div class="flex gap-2">
<button class="p-2 hover:bg-surface-container-high rounded-lg text-outline transition-colors"><span class="material-symbols-outlined text-sm">filter_list</span></button>
<button class="p-2 hover:bg-surface-container-high rounded-lg text-outline transition-colors"><span class="material-symbols-outlined text-sm">download</span></button>
</div>
</div>
<div class="min-h-[400px] flex flex-col">
<!-- Table Header -->
<div class="grid grid-cols-12 gap-4 px-8 py-3 bg-surface-container-high/30 border-b border-outline-variant/5">
<div class="col-span-3 text-[10px] uppercase font-label tracking-widest text-outline">Name</div>
<div class="col-span-3 text-[10px] uppercase font-label tracking-widest text-outline">Subnet</div>
<div class="col-span-4 text-[10px] uppercase font-label tracking-widest text-outline">Description</div>
<div class="col-span-2 text-[10px] uppercase font-label tracking-widest text-outline text-right">Default</div>
</div>
<!-- Empty State Content -->
<div class="flex-1 flex flex-col items-center justify-center py-20 px-4 text-center">
<div class="relative mb-8">
<div class="w-24 h-24 rounded-full bg-surface-container-high flex items-center justify-center animate-pulse">
<span class="material-symbols-outlined text-5xl text-outline/30">lan</span>
</div>
<div class="absolute -right-2 -bottom-2 w-10 h-10 rounded-full bg-surface border-4 border-surface-container flex items-center justify-center">
<span class="material-symbols-outlined text-tertiary text-lg">question_mark</span>
</div>
</div>
<h4 class="font-headline text-2xl font-bold mb-3">No networks yet</h4>
<p class="text-outline max-w-sm font-body text-sm leading-relaxed mb-8">
                                You haven't configured any VPN tunnel subnets. Start by adding a new network to route traffic between your peers securely.
                            </p>
<div class="flex gap-4">
<button class="px-6 py-2.5 rounded-lg font-label text-xs uppercase tracking-tight border border-outline-variant/20 hover:bg-surface-container-high transition-all">View Documentation</button>
<button class="px-6 py-2.5 rounded-lg font-label text-xs uppercase tracking-tight bg-primary-container text-on-primary-container hover:shadow-lg hover:shadow-primary-container/20 transition-all">Add First Network</button>
</div>
</div>
</div>
</div>
</div>
<!-- Contextual Insight Card -->
<div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
<div class="glass-panel p-8 rounded-2xl border-t border-white/5 flex flex-col gap-4">
<span class="material-symbols-outlined text-primary text-3xl">lightbulb</span>
<h5 class="font-headline font-bold">Network Best Practices</h5>
<p class="text-sm text-outline leading-relaxed font-body">We recommend using the 100.64.0.0/10 range (Carrier Grade NAT) to avoid conflicts with common home or office networks like 192.168.0.0/16.</p>
</div>
<div class="relative group h-full">
<div class="absolute inset-0 bg-gradient-to-br from-primary-container/20 to-tertiary-container/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
<div class="relative h-full bg-surface-container-low/40 border border-outline-variant/10 p-8 rounded-2xl flex flex-col justify-between">
<div>
<span class="material-symbols-outlined text-tertiary text-3xl mb-4">auto_awesome</span>
<h5 class="font-headline font-bold mb-2">Auto-Orchestration</h5>
<p class="text-sm text-outline leading-relaxed font-body">Enable automatic subnet assignment to let NetLoom intelligently manage your IP space without collisions.</p>
</div>
<a class="mt-6 flex items-center gap-2 text-xs font-label text-tertiary font-bold uppercase tracking-widest group-hover:gap-4 transition-all" href="#">
                            Configure Auto-Flow <span class="material-symbols-outlined text-sm">arrow_forward</span>
</a>
</div>
</div>
<div class="bg-surface-container-high/40 p-8 rounded-2xl border border-outline-variant/10 flex flex-col justify-center items-center text-center">
<img alt="Globe Icon" class="mb-4 opacity-50 grayscale" data-alt="Stylized wireframe globe representing a global network mesh with glowing nodes and interconnecting lines in a dark tech aesthetic" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCC8r-Qvg3VcoNx4rmwPdrmQgy2c7p5jEOzkEI_XO2s5VejTTeUe4fv2H7IHifeitHV2j_785hPYxXJRmKYnFoOUVqLdIR3LhYrZcXLev_V1h8MLLMYD2tAvsCRcf-0loxeZ7ThAamniN2oC0ZR5gtbq9jm0hSK6vlQSbf591VKtrcbCVKzbWw7tj51pS97x_5p28e_K4udxWDI5oC3BijEBrPGbDvG1PqlnAPTJdqU-ywf-2iw2EdXqoHCxvBogizF00KH5XEZsFE"/>
<p class="text-xs font-label text-outline/60 uppercase tracking-tighter">Scale your infrastructure</p>
<p class="font-headline font-bold text-on-surface-variant">Global Mesh Ready</p>
</div>
</div>
</div>
<!-- BottomNavBar Shell -->
<footer class="fixed bottom-0 right-0 w-[calc(100%-16rem)] h-8 bg-[#110f2f] flex justify-end gap-6 px-8 items-center z-50 border-t border-[#474555]/15">
<div class="flex items-center gap-2 text-[#00daf3] animate-pulse">
<span class="material-symbols-outlined text-[14px]">database</span>
<span class="font-label font-medium text-[10px] uppercase tracking-widest">DB: Connected</span>
</div>
<div class="flex items-center gap-2 text-[#928ea1] opacity-60">
<span class="material-symbols-outlined text-[14px]">vpn_lock</span>
<span class="font-label font-medium text-[10px] uppercase tracking-widest">WG: Active</span>
</div>
</footer>
</main>
</body></html>

<!-- Peers (Updated) -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&amp;family=Space+Grotesk:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
              "surface-tint": "#c7bfff",
              "on-primary": "#29009f",
              "primary": "#c7bfff",
              "surface-container-highest": "#333152",
              "surface-dim": "#110f2f",
              "on-primary-fixed": "#170065",
              "primary-fixed-dim": "#c7bfff",
              "tertiary-fixed": "#9cf0ff",
              "surface-container-lowest": "#0c092a",
              "on-tertiary-fixed-variant": "#004f58",
              "inverse-on-surface": "#2e2d4e",
              "inverse-surface": "#e3dfff",
              "primary-container": "#624af4",
              "outline-variant": "#474555",
              "on-secondary-container": "#b7b5d7",
              "secondary-fixed-dim": "#c5c3e5",
              "surface-container-low": "#191838",
              "primary-fixed": "#e4dfff",
              "tertiary-fixed-dim": "#00daf3",
              "on-tertiary": "#00363d",
              "on-surface-variant": "#c8c4d8",
              "tertiary": "#00daf3",
              "on-secondary-fixed": "#191933",
              "error-container": "#93000a",
              "tertiary-container": "#007482",
              "secondary": "#c5c3e5",
              "on-primary-container": "#ebe6ff",
              "on-secondary": "#2e2e49",
              "surface-container-high": "#282647",
              "surface": "#110f2f",
              "on-surface": "#e3dfff",
              "background": "#110f2f",
              "on-error": "#690005",
              "secondary-container": "#474663",
              "secondary-fixed": "#e2dfff",
              "on-tertiary-fixed": "#001f24",
              "outline": "#928ea1",
              "surface-container": "#1d1c3c",
              "surface-variant": "#333152",
              "on-background": "#e3dfff",
              "surface-bright": "#373557",
              "on-secondary-fixed-variant": "#444460",
              "inverse-primary": "#573de9",
              "on-tertiary-container": "#b8f4ff",
              "on-error-container": "#ffdad6",
              "error": "#ffb4ab",
              "on-primary-fixed-variant": "#3e15d2"
            },
            fontFamily: {
              "headline": ["Inter"],
              "body": ["Inter"],
              "label": ["Space Grotesk"]
            },
            borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
          },
        },
      }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
        }
        body {
            background-color: #110f2f;
            color: #e3dfff;
            font-family: 'Inter', sans-serif;
        }
        .glass-card {
            background: rgba(29, 28, 60, 0.4);
            backdrop-filter: blur(12px);
            border-top: 1px solid rgba(71, 69, 85, 0.15);
        }
    </style>
</head>
<body class="bg-surface text-on-surface">
<!-- SideNavBar (Authority: JSON & Design System) -->
<aside class="fixed left-0 top-0 h-full flex flex-col py-6 bg-[#1d1c3c] dark:bg-[#1d1c3c] w-64 z-40">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tighter text-[#e3dfff] font-headline">NetLoom</h1>
<p class="font-label text-xs tracking-tight text-outline">Orchestrator v1.0</p>
</div>
<nav class="flex-1 flex flex-col">
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined" data-icon="dashboard">dashboard</span> Dashboard
            </a>
<!-- Active Item: Peers -->
<a class="bg-[#282647] text-[#00daf3] rounded-lg mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-all duration-300 scale-95 active:scale-90" href="#">
<span class="material-symbols-outlined" data-icon="hub">hub</span> Peers
            </a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined" data-icon="lan">lan</span> Networks
            </a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined" data-icon="security">security</span> Zones
            </a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined" data-icon="group">group</span> Groups
            </a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined" data-icon="policy">policy</span> Policies
            </a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 font-label text-xs tracking-tight transition-colors hover:bg-[#282647]/50" href="#">
<span class="material-symbols-outlined" data-icon="settings">settings</span> System
            </a>
</nav>
<div class="px-6 pt-6 mt-auto flex items-center gap-3">
<div class="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-xs font-bold overflow-hidden">
<img alt="Admin User" data-alt="close-up portrait of professional male admin user with neutral expression against dark studio background" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDOlJZW_D3xIwTwNJrco9Cc1gUSWazjVjDtDpjkQWh8Y3csP93xhfPfQQ_TYvPkEDXYFsfKO8LE9Rjsm76vsr0D8jvdv8Bt3N2QwMr-l_StGV8ffdNNS6SqG6VfDH7VtsPd_Vnqc4sqnJSxVpwklGw_J23uh3ni1z1XxV9lfM6ElcBuU36A2mmqEs7YBoLSGBVtlQPYFv-LPcps7_--qClvnEyWlCbLV5Pn_QDoLxVA41ueL_ZIbrOUZgD9Fj1vhiOctJH-11fEqEA"/>
</div>
<div class="flex flex-col">
<span class="text-xs font-semibold font-headline">Admin User</span>
<span class="text-[10px] font-label text-outline uppercase tracking-wider">Superuser</span>
</div>
</div>
</aside>
<!-- TopNavBar -->
<header class="flex justify-between items-center h-16 px-8 ml-64 w-[calc(100%-16rem)] bg-[#110f2f]/80 backdrop-blur-xl fixed top-0 z-30">
<div class="flex items-center gap-4">
<h2 class="font-headline font-bold text-lg text-on-surface">Peers</h2>
</div>
<div class="flex items-center gap-6">
<div class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm" data-icon="search">search</span>
<input class="bg-surface-container-low border-none rounded-lg pl-10 pr-4 py-2 text-sm font-label focus:ring-1 focus:ring-primary w-64" placeholder="Search peers..." type="text"/>
</div>
<div class="flex items-center gap-4 text-outline">
<span class="material-symbols-outlined cursor-pointer hover:text-primary transition-opacity" data-icon="dark_mode">dark_mode</span>
<span class="material-symbols-outlined cursor-pointer hover:text-primary transition-opacity" data-icon="notifications">notifications</span>
</div>
</div>
</header>
<!-- Main Content Canvas -->
<main class="ml-64 pt-24 px-8 pb-16 min-h-screen">
<!-- Header Actions -->
<div class="flex justify-between items-end mb-10">
<div>
<h3 class="font-headline font-extrabold text-3xl tracking-tight mb-2">Network Inventory</h3>
<p class="text-outline max-w-xl">Manage secure endpoints and cross-site connections within the NetLoom fabric. Orchestrate zero-trust access across distributed architectures.</p>
</div>
<div class="flex gap-4">
<button class="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-outline-variant/15 font-label text-sm font-medium hover:bg-surface-container-high transition-colors active:scale-95">
<span class="material-symbols-outlined text-tertiary" data-icon="add_business">add_business</span>
                    + Branch Office
                </button>
<button class="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary-container text-on-primary-container font-label text-sm font-semibold shadow-lg shadow-primary-container/20 transition-all hover:opacity-90 active:scale-95">
<span class="material-symbols-outlined" data-icon="person_add">person_add</span>
                    + RoadWarrior
                </button>
</div>
</div>
<!-- Peers Table Component -->
<div class="bg-surface-container-low rounded-xl overflow-hidden shadow-2xl">
<table class="w-full text-left border-collapse">
<thead>
<tr class="bg-surface-container-high/50 font-label text-[10px] uppercase tracking-[0.2em] text-outline">
<th class="px-6 py-4 font-semibold">Peer Name</th>
<th class="px-6 py-4 font-semibold">Type</th>
<th class="px-6 py-4 font-semibold text-center">Protocol</th>
<th class="px-6 py-4 font-semibold">Internal IP</th>
<th class="px-6 py-4 font-semibold">Shared LAN</th>
<th class="px-6 py-4 font-semibold">Tunnel</th>
<th class="px-6 py-4 font-semibold text-center">Status</th>
<th class="px-6 py-4 font-semibold text-right">Operations</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/5">
<!-- Row 1 -->
<tr class="group hover:bg-surface-container-high transition-colors cursor-default">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center text-tertiary">
<span class="material-symbols-outlined" data-icon="person">person</span>
</div>
<div>
<div class="font-semibold text-sm">Juan Dolan</div>
<div class="text-[10px] text-outline font-label">Engineering (Remote)</div>
</div>
</div>
</td>
<td class="px-6 py-5">
<span class="text-xs px-2 py-1 rounded bg-surface-container-highest text-secondary font-label">Roadwarrior</span>
</td>
<td class="px-6 py-5 text-center">
<span class="material-symbols-outlined text-outline text-sm" data-icon="encrypted">encrypted</span>
</td>
<td class="px-6 py-5">
<code class="font-label text-xs text-tertiary-fixed-dim bg-tertiary/5 px-2 py-1 rounded">10.1.1.2/32</code>
</td>
<td class="px-6 py-5">
<span class="text-xs text-outline font-label italic">N/A</span>
</td>
<td class="px-6 py-5 text-sm">Split Tunnel</td>
<td class="px-6 py-5">
<div class="flex justify-center">
<div class="w-10 h-5 bg-tertiary/20 rounded-full p-1 flex items-center justify-end cursor-pointer">
<div class="w-3 h-3 bg-tertiary rounded-full shadow-[0_0_8px_rgba(0,218,243,0.6)]"></div>
</div>
</div>
</td>
<td class="px-6 py-5">
<div class="flex justify-end gap-2 opacity-40 group-hover:opacity-100 transition-opacity">
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface" title="Shield"><span class="material-symbols-outlined text-sm" data-icon="shield">shield</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface" title="Download"><span class="material-symbols-outlined text-sm" data-icon="download">download</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface" title="QR Code"><span class="material-symbols-outlined text-sm" data-icon="qr_code">qr_code</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface" title="Reset"><span class="material-symbols-outlined text-sm" data-icon="restart_alt">restart_alt</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-error" title="Delete"><span class="material-symbols-outlined text-sm" data-icon="delete">delete</span></button>
</div>
</td>
</tr>
<!-- Row 2 -->
<tr class="group hover:bg-surface-container-high transition-colors cursor-default">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
<span class="material-symbols-outlined" data-icon="apartment">apartment</span>
</div>
<div>
<div class="font-semibold text-sm">Suc Rosario</div>
<div class="text-[10px] text-outline font-label">DR Site (Azure)</div>
</div>
</div>
</td>
<td class="px-6 py-5">
<span class="text-xs px-2 py-1 rounded bg-surface-container-highest text-secondary font-label">Branch Office</span>
</td>
<td class="px-6 py-5 text-center">
<span class="material-symbols-outlined text-outline text-sm" data-icon="link">link</span>
</td>
<td class="px-6 py-5">
<code class="font-label text-xs text-tertiary-fixed-dim bg-tertiary/5 px-2 py-1 rounded">10.40.1.1/32</code>
</td>
<td class="px-6 py-5">
<code class="font-label text-xs text-secondary bg-secondary/5 px-2 py-1 rounded">10.40.1.0/24</code>
</td>
<td class="px-6 py-5 text-sm">Full Tunnel</td>
<td class="px-6 py-5">
<div class="flex justify-center">
<div class="w-10 h-5 bg-tertiary/20 rounded-full p-1 flex items-center justify-end cursor-pointer">
<div class="w-3 h-3 bg-tertiary rounded-full shadow-[0_0_8px_rgba(0,218,243,0.6)]"></div>
</div>
</div>
</td>
<td class="px-6 py-5">
<div class="flex justify-end gap-2 opacity-40 group-hover:opacity-100 transition-opacity">
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="shield">shield</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="download">download</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="qr_code">qr_code</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="power_settings_new">power_settings_new</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-error"><span class="material-symbols-outlined text-sm" data-icon="delete">delete</span></button>
</div>
</td>
</tr>
<!-- Row 3 -->
<tr class="group hover:bg-surface-container-high transition-colors cursor-default">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center text-tertiary">
<span class="material-symbols-outlined" data-icon="person">person</span>
</div>
<div>
<div class="font-semibold text-sm">Elias Vance</div>
<div class="text-[10px] text-outline font-label">DevOps (Mobile)</div>
</div>
</div>
</td>
<td class="px-6 py-5">
<span class="text-xs px-2 py-1 rounded bg-surface-container-highest text-secondary font-label">Roadwarrior</span>
</td>
<td class="px-6 py-5 text-center">
<span class="material-symbols-outlined text-outline text-sm" data-icon="encrypted">encrypted</span>
</td>
<td class="px-6 py-5">
<code class="font-label text-xs text-tertiary-fixed-dim bg-tertiary/5 px-2 py-1 rounded">10.1.1.8/32</code>
</td>
<td class="px-6 py-5">
<span class="text-xs text-outline font-label italic">N/A</span>
</td>
<td class="px-6 py-5 text-sm">Split Tunnel</td>
<td class="px-6 py-5">
<div class="flex justify-center">
<div class="w-10 h-5 bg-outline-variant/30 rounded-full p-1 flex items-center justify-start cursor-pointer">
<div class="w-3 h-3 bg-outline rounded-full"></div>
</div>
</div>
</td>
<td class="px-6 py-5">
<div class="flex justify-end gap-2 opacity-40 group-hover:opacity-100 transition-opacity">
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="shield">shield</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="download">download</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="qr_code">qr_code</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="restart_alt">restart_alt</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-error"><span class="material-symbols-outlined text-sm" data-icon="delete">delete</span></button>
</div>
</td>
</tr>
<!-- Row 4 -->
<tr class="group hover:bg-surface-container-high transition-colors cursor-default">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
<span class="material-symbols-outlined" data-icon="apartment">apartment</span>
</div>
<div>
<div class="font-semibold text-sm">Berlin Hub</div>
<div class="text-[10px] text-outline font-label">HQ Office (Fiber)</div>
</div>
</div>
</td>
<td class="px-6 py-5">
<span class="text-xs px-2 py-1 rounded bg-surface-container-highest text-secondary font-label">Branch Office</span>
</td>
<td class="px-6 py-5 text-center">
<span class="material-symbols-outlined text-outline text-sm" data-icon="link">link</span>
</td>
<td class="px-6 py-5">
<code class="font-label text-xs text-tertiary-fixed-dim bg-tertiary/5 px-2 py-1 rounded">172.16.0.1/32</code>
</td>
<td class="px-6 py-5">
<code class="font-label text-xs text-secondary bg-secondary/5 px-2 py-1 rounded">172.16.0.0/20</code>
</td>
<td class="px-6 py-5 text-sm">Full Tunnel</td>
<td class="px-6 py-5">
<div class="flex justify-center">
<div class="w-10 h-5 bg-tertiary/20 rounded-full p-1 flex items-center justify-end cursor-pointer">
<div class="w-3 h-3 bg-tertiary rounded-full shadow-[0_0_8px_rgba(0,218,243,0.6)]"></div>
</div>
</div>
</td>
<td class="px-6 py-5">
<div class="flex justify-end gap-2 opacity-40 group-hover:opacity-100 transition-opacity">
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="shield">shield</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="download">download</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="qr_code">qr_code</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-on-surface"><span class="material-symbols-outlined text-sm" data-icon="power_settings_new">power_settings_new</span></button>
<button class="p-2 hover:bg-surface-bright rounded-lg text-outline-variant hover:text-error"><span class="material-symbols-outlined text-sm" data-icon="delete">delete</span></button>
</div>
</td>
</tr>
</tbody>
</table>
<!-- Table Footer -->
<div class="bg-surface-container-high/30 px-6 py-4 flex items-center justify-between font-label">
<div class="text-[10px] text-outline uppercase tracking-widest">Showing 4 of 4 peers</div>
<div class="flex gap-2">
<button class="p-2 rounded hover:bg-surface-container-highest transition-colors opacity-50"><span class="material-symbols-outlined text-sm" data-icon="chevron_left">chevron_left</span></button>
<button class="p-2 rounded bg-primary-container/20 text-primary transition-colors"><span class="material-symbols-outlined text-sm" data-icon="chevron_right">chevron_right</span></button>
</div>
</div>
</div>
<!-- Network Topology Preview (Asymmetric Design System Element) -->
<div class="mt-12 grid grid-cols-12 gap-8">
<div class="col-span-8 glass-card rounded-xl p-8 relative overflow-hidden group">
<div class="absolute top-0 right-0 p-8 opacity-20 group-hover:opacity-40 transition-opacity">
<span class="material-symbols-outlined text-7xl text-tertiary" data-icon="hub">hub</span>
</div>
<h4 class="font-headline font-bold text-xl mb-4">Fabric Connectivity</h4>
<p class="text-sm text-outline mb-6 max-w-lg">Real-time mesh visualization of active peer tunnels. Connections are cryptographically isolated via the NetLoom Orchestration Layer.</p>
<div class="h-48 bg-surface-container-lowest rounded-lg border border-outline-variant/5 flex items-center justify-center">
<div class="flex flex-col items-center gap-4 text-outline-variant">
<span class="material-symbols-outlined text-4xl" data-icon="map">map</span>
<span class="font-label text-[10px] tracking-widest uppercase">Topology Visualization Not Active</span>
</div>
</div>
</div>
<div class="col-span-4 flex flex-col gap-6">
<div class="bg-surface-container-low p-6 rounded-xl">
<div class="flex items-center justify-between mb-4">
<span class="font-label text-[10px] uppercase tracking-widest text-outline">Network Health</span>
<span class="w-2 h-2 rounded-full bg-tertiary animate-pulse shadow-[0_0_8px_rgba(0,218,243,0.8)]"></span>
</div>
<div class="text-2xl font-headline font-bold">99.98%</div>
<div class="text-[10px] text-tertiary font-label mt-1">Operational Fabric</div>
</div>
<div class="bg-surface-container-low p-6 rounded-xl">
<div class="flex items-center justify-between mb-4">
<span class="font-label text-[10px] uppercase tracking-widest text-outline">Traffic (24h)</span>
<span class="material-symbols-outlined text-primary text-sm" data-icon="trending_up">trending_up</span>
</div>
<div class="text-2xl font-headline font-bold">1.4 TB</div>
<div class="text-[10px] text-outline font-label mt-1">Cross-site throughput</div>
</div>
</div>
</div>
</main>
<!-- Bottom Status Bar (Authority: JSON & Design System) -->
<footer class="fixed bottom-0 right-0 w-[calc(100%-16rem)] h-8 bg-[#110f2f] border-t border-[#474555]/15 flex justify-end gap-6 px-8 items-center z-50">
<div class="flex items-center gap-2 text-[#00daf3] animate-pulse font-label text-[10px] uppercase tracking-widest">
<span class="material-symbols-outlined text-xs" data-icon="database">database</span> DB: Connected
        </div>
<div class="flex items-center gap-2 text-[#00daf3] animate-pulse font-label text-[10px] uppercase tracking-widest">
<span class="material-symbols-outlined text-xs" data-icon="vpn_lock">vpn_lock</span> WG: Active
        </div>
</footer>
</body></html>

<!-- Groups -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&amp;family=Space+Grotesk:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
              "surface-tint": "#c7bfff",
              "on-primary": "#29009f",
              "primary": "#c7bfff",
              "surface-container-highest": "#333152",
              "surface-dim": "#110f2f",
              "on-primary-fixed": "#170065",
              "primary-fixed-dim": "#c7bfff",
              "tertiary-fixed": "#9cf0ff",
              "surface-container-lowest": "#0c092a",
              "on-tertiary-fixed-variant": "#004f58",
              "inverse-on-surface": "#2e2d4e",
              "inverse-surface": "#e3dfff",
              "primary-container": "#624af4",
              "outline-variant": "#474555",
              "on-secondary-container": "#b7b5d7",
              "secondary-fixed-dim": "#c5c3e5",
              "surface-container-low": "#191838",
              "primary-fixed": "#e4dfff",
              "tertiary-fixed-dim": "#00daf3",
              "on-tertiary": "#00363d",
              "on-surface-variant": "#c8c4d8",
              "tertiary": "#00daf3",
              "on-secondary-fixed": "#191933",
              "error-container": "#93000a",
              "tertiary-container": "#007482",
              "secondary": "#c5c3e5",
              "on-primary-container": "#ebe6ff",
              "on-secondary": "#2e2e49",
              "surface-container-high": "#282647",
              "surface": "#110f2f",
              "on-surface": "#e3dfff",
              "background": "#110f2f",
              "on-error": "#690005",
              "secondary-container": "#474663",
              "secondary-fixed": "#e2dfff",
              "on-tertiary-fixed": "#001f24",
              "outline": "#928ea1",
              "surface-container": "#1d1c3c",
              "surface-variant": "#333152",
              "on-background": "#e3dfff",
              "surface-bright": "#373557",
              "on-secondary-fixed-variant": "#444460",
              "inverse-primary": "#573de9",
              "on-tertiary-container": "#b8f4ff",
              "on-error-container": "#ffdad6",
              "error": "#ffb4ab",
              "on-primary-fixed-variant": "#3e15d2"
            },
            fontFamily: {
              "headline": ["Inter"],
              "body": ["Inter"],
              "label": ["Space Grotesk"]
            },
            borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
          },
        },
      }
    </script>
<style>
      .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
      }
      .no-scrollbar::-webkit-scrollbar { display: none; }
      .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-surface text-on-surface font-body selection:bg-primary/30">
<!-- SideNavBar -->
<nav class="fixed left-0 top-0 h-full flex flex-col py-6 bg-[#1d1c3c] dark:bg-[#1d1c3c] w-64 z-50">
<div class="px-6 mb-10 flex items-center gap-3">
<div class="w-8 h-8 rounded bg-gradient-to-br from-primary-container to-tertiary flex items-center justify-center shadow-lg shadow-primary-container/20">
<span class="material-symbols-outlined text-on-primary-container text-xl" style="font-variation-settings: 'FILL' 1;">hub</span>
</div>
<div>
<h1 class="font-headline font-bold tracking-tighter text-xl text-[#e3dfff]">NetLoom</h1>
<p class="font-label text-[10px] uppercase tracking-widest text-outline">Orchestrator v1.0</p>
</div>
</div>
<div class="flex-1 space-y-1">
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-colors" href="#">
<span class="material-symbols-outlined">dashboard</span>
<span class="font-label text-xs tracking-tight">Dashboard</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-colors" href="#">
<span class="material-symbols-outlined">hub</span>
<span class="font-label text-xs tracking-tight">Peers</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-colors" href="#">
<span class="material-symbols-outlined">lan</span>
<span class="font-label text-xs tracking-tight">Networks</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-colors" href="#">
<span class="material-symbols-outlined">security</span>
<span class="font-label text-xs tracking-tight">Zones</span>
</a>
<!-- Active Tab: Groups -->
<a class="bg-[#282647] text-[#00daf3] rounded-lg mx-2 my-1 px-4 py-3 flex items-center gap-3 transition-all duration-300" href="#">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">group</span>
<span class="font-label text-xs tracking-tight">Groups</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-colors" href="#">
<span class="material-symbols-outlined">policy</span>
<span class="font-label text-xs tracking-tight">Policies</span>
</a>
<a class="text-[#928ea1] hover:text-[#e3dfff] mx-2 my-1 px-4 py-3 flex items-center gap-3 hover:bg-[#282647]/50 transition-colors" href="#">
<span class="material-symbols-outlined">settings</span>
<span class="font-label text-xs tracking-tight">System</span>
</a>
</div>
<div class="mt-auto px-6 py-4 flex items-center gap-3 border-t border-outline-variant/10">
<img alt="Admin User" class="w-8 h-8 rounded-full border border-primary-container/30" data-alt="close up professional portrait of a tech administrator with clean studio lighting and soft bokeh background" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBoo5A1iCoViiWcoh7rlSvZSWhmmpvB_bdJagPUpKz6AMi2eGnsiKKpo0FzWYi--v9nkiIDtHhquwMR3vdkVZjpBx2I1SvOxKLwTVZH2pE7asPUJ7kPnb3sYr7o02_A--PBG70dbhvIgv8tIYvqgZGNBGyTHdR89ZFtuPCJWmeC0UGkPtpiyxwa7HLUaxiP1IZ6CJeuRmu6NaAkc_xW5lJ_QfsDqefjn53X2qLkhwQhcNciD_yfvcdFc4g1WpB1TdmAIfQIIgUXMS8"/>
<div class="overflow-hidden">
<p class="font-headline font-semibold text-xs text-on-surface truncate">Admin User</p>
<p class="font-label text-[10px] text-outline truncate">Superuser</p>
</div>
</div>
</nav>
<!-- TopNavBar -->
<header class="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 px-8 flex justify-between items-center bg-[#110f2f]/80 backdrop-blur-xl z-40">
<div class="flex items-center gap-4">
<h2 class="font-headline font-bold text-lg text-on-surface">Groups</h2>
<div class="h-4 w-px bg-outline-variant/30"></div>
<p class="font-label text-sm text-outline">Manage peer access profiles</p>
</div>
<div class="flex items-center gap-6">
<div class="relative group">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline group-focus-within:text-tertiary transition-colors">search</span>
<input class="bg-surface-container-low border-none rounded-lg pl-10 pr-4 py-2 text-sm w-64 focus:ring-1 focus:ring-tertiary/50 transition-all font-body" placeholder="Search groups..." type="text"/>
</div>
<div class="flex items-center gap-2">
<button class="p-2 rounded-full text-outline hover:text-on-surface hover:bg-surface-container-high transition-all active:opacity-70">
<span class="material-symbols-outlined">dark_mode</span>
</button>
<button class="p-2 rounded-full text-outline hover:text-on-surface hover:bg-surface-container-high transition-all active:opacity-70 relative">
<span class="material-symbols-outlined">notifications</span>
<span class="absolute top-2 right-2 w-2 h-2 bg-tertiary rounded-full shadow-[0_0_8px_rgba(0,218,243,0.6)]"></span>
</button>
</div>
</div>
</header>
<!-- Main Content Canvas -->
<main class="ml-64 pt-24 pb-16 px-8 min-h-screen">
<!-- Action Header -->
<div class="flex justify-between items-end mb-8">
<div class="space-y-1">
<span class="font-label text-[10px] uppercase tracking-[0.2em] text-tertiary font-semibold">Security Architecture</span>
<h3 class="font-headline font-extrabold text-3xl tracking-tight text-on-surface">Access Profiles</h3>
</div>
<button class="flex items-center gap-2 bg-primary-container text-on-primary-container px-5 py-2.5 rounded-lg font-headline font-bold text-sm shadow-lg shadow-primary-container/20 hover:scale-[1.02] active:scale-95 transition-all">
<span class="material-symbols-outlined text-lg">add</span>
                + Add Group
            </button>
</div>
<!-- Groups Management Table Container -->
<div class="bg-surface-container rounded-xl overflow-hidden shadow-2xl shadow-black/20">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead>
<tr class="bg-surface-container-low">
<th class="px-6 py-4 font-label text-xs uppercase tracking-widest text-outline">Name</th>
<th class="px-6 py-4 font-label text-xs uppercase tracking-widest text-outline">Description</th>
<th class="px-6 py-4 font-label text-xs uppercase tracking-widest text-outline">Members</th>
<th class="px-6 py-4 font-label text-xs uppercase tracking-widest text-outline text-right">Actions</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/10">
<!-- Row 1 -->
<tr class="group hover:bg-surface-container-high transition-colors">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center justify-center text-primary-container">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">admin_panel_settings</span>
</div>
<div>
<p class="font-headline font-semibold text-on-surface">Admin</p>
<p class="font-label text-[10px] text-tertiary">ROOT_ACCESS</p>
</div>
</div>
</td>
<td class="px-6 py-5">
<p class="text-sm text-on-surface-variant max-w-xs truncate">Full infrastructure management and orchestration permissions.</p>
</td>
<td class="px-6 py-5">
<div class="flex items-center gap-2">
<span class="font-label text-sm text-on-surface">3 peers</span>
<div class="flex -space-x-2">
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="professional user avatar of a smiling man with glasses in casual tech attire" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCTC7GMf2G7dr7A-JZDu-sErgPcWOy3Q8GVQgsKTItBQ2lTrI9vZmFc7JKT27lSN1T6yjoR3oj6-kigNuCPJNonpEOICT3sn7HI4wIeIrzvgHiYPo5LWuKqgfnliXrb155PwNUKpSGzPJbMVKrk8wIVFeN9UfJ1YIKWHepjQYxoe-wHnVgnokE6TAbINQvwb-PgL5ZlDb67PkA5SEURAH-QuO4Wo6QXykOMO-2NFA2Z4MCDsoAOBSmQhD_C9wBrtWwqPtd-Htuhe1s"/>
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="professional user avatar of a woman with short hair in business casual attire" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDIPP14DHVg2Y5GIEGC-5sjEN6j17hfPDMWRW4LnNXuut-z3InpNgS1D6untFgEFk0oRfzfK6eMtPQb4YQZoWsSiQS02rizI8FqyeNd2DzfkOEjuvdX42LTH_SXTRcw1NQvBPwuDKEQi-K9-raeWvgXJ6IbWXU6V6dnJwysd9ilgRK88Z0a6AqP-SUWb6Kvgp9kfPEyFXzSgBBilPhMFJWJY9ptx1Pkwd6lO59jba8SqbAfEPD-jOAqVrcJuowV2FRvbHXsAqgrA8I"/>
<div class="w-6 h-6 rounded-full border-2 border-surface-container bg-surface-container-highest flex items-center justify-center text-[8px] font-bold text-outline">+1</div>
</div>
</div>
</td>
<td class="px-6 py-5 text-right">
<div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-2 rounded-lg text-outline hover:text-tertiary hover:bg-tertiary/10 transition-colors">
<span class="material-symbols-outlined text-xl">group</span>
</button>
<button class="p-2 rounded-lg text-outline hover:text-error hover:bg-error/10 transition-colors">
<span class="material-symbols-outlined text-xl">delete</span>
</button>
</div>
</td>
</tr>
<!-- Row 2 -->
<tr class="group hover:bg-surface-container-high transition-colors">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center text-tertiary">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">developer_board</span>
</div>
<div>
<p class="font-headline font-semibold text-on-surface">Engineering</p>
<p class="font-label text-[10px] text-tertiary">DEV_ACCESS</p>
</div>
</div>
</td>
<td class="px-6 py-5">
<p class="text-sm text-on-surface-variant max-w-xs truncate">Access to development clusters and staging environments.</p>
</td>
<td class="px-6 py-5">
<div class="flex items-center gap-2">
<span class="font-label text-sm text-on-surface">12 peers</span>
<div class="flex -space-x-2">
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="modern tech worker avatar with headphones around neck" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBn92g3T7_k7uBR5OrA71ZqL8I8aM-VsnJRsD3-yOBXUsaZn17jt-oPSj0BPsoYAZ02jnA5BtmeSZ7NuB6s49oRwjP1kee7VmoP_lT2U8pEN9cqN8aieG0qG51ixbFWLZASyROy1QVBS1B30AGp8dr_XjpdOUJfxN7NARt9PdVfLrwIrpgM_HuIkGzuI-bEI_IrrJty6O2ygtnkimKztt98a-MwuquGoKc9Xqcl_Qf-Nmz1A4f8zY2uuKSvT3z_S0aSowhbdhGreRU"/>
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="software engineer avatar with beard and minimalist glasses" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAUF7yM5dkvQ5gtxu1vn7IFAbWTO5n1OofkMXR54-s_jWt9DHb_zoqokx3jcHYZEPcxRkCjZj1qd1OnM_b6AVQ9PelBbMADbeV3gu__zH12ZSy_k0GvwhQxGpbiKyGKKaeNcshDe45mhONvJpuxZPhe51HU3_VWXvp7ysQaIQ8MEuaLHeUsYqO7vRHh8HVfrykwy9aOT2OzTzczHLSeTh2YoY7u3A7UHFK2XBm3PEcXDr-iR_x0jjc_QDXAe9hpv7jfXOnqd6tTMGI"/>
<div class="w-6 h-6 rounded-full border-2 border-surface-container bg-surface-container-highest flex items-center justify-center text-[8px] font-bold text-outline">+10</div>
</div>
</div>
</td>
<td class="px-6 py-5 text-right">
<div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-2 rounded-lg text-outline hover:text-tertiary hover:bg-tertiary/10 transition-colors">
<span class="material-symbols-outlined text-xl">group</span>
</button>
<button class="p-2 rounded-lg text-outline hover:text-error hover:bg-error/10 transition-colors">
<span class="material-symbols-outlined text-xl">delete</span>
</button>
</div>
</td>
</tr>
<!-- Row 3 -->
<tr class="group hover:bg-surface-container-high transition-colors">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-outline-variant/10 flex items-center justify-center text-outline">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">cloud_queue</span>
</div>
<div>
<p class="font-headline font-semibold text-on-surface">Guest</p>
<p class="font-label text-[10px] text-outline">READ_ONLY</p>
</div>
</div>
</td>
<td class="px-6 py-5">
<p class="text-sm text-on-surface-variant max-w-xs truncate">Temporary read-only access for external audit teams.</p>
</td>
<td class="px-6 py-5">
<div class="flex items-center gap-2">
<span class="font-label text-sm text-on-surface">1 peer</span>
<div class="flex">
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="guest user avatar with neutral expression and simple background" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAEYszLuREYH_KREWiZ4OrUdFrZb9IatYh12kOYp095i_LdNvNvYnkch1UrSp6s_y1_czssJJYnwayfsMkJGtGZTL0sA0sKW1B2WOsDSCH7ImFzMCIGSbiejlfVikbZhWlWbdels8CsAVNZU_eJsyxKDXENLJ19HajVnf1yflNJh5CDdclSnD29-LwmVPQrnJUiCQqLmGKXvtbtkqu4hh0uUB1vTZeCsg2IWS62VK9h2L17g2PXdj6ykXdZ9t5PhqAakVbDv5EPtWc"/>
</div>
</div>
</td>
<td class="px-6 py-5 text-right">
<div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-2 rounded-lg text-outline hover:text-tertiary hover:bg-tertiary/10 transition-colors">
<span class="material-symbols-outlined text-xl">group</span>
</button>
<button class="p-2 rounded-lg text-outline hover:text-error hover:bg-error/10 transition-colors">
<span class="material-symbols-outlined text-xl">delete</span>
</button>
</div>
</td>
</tr>
<!-- Row 4 -->
<tr class="group hover:bg-surface-container-high transition-colors">
<td class="px-6 py-5">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-error/10 flex items-center justify-center text-error">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">security</span>
</div>
<div>
<p class="font-headline font-semibold text-on-surface">Security Operations</p>
<p class="font-label text-[10px] text-error">SOC_LEVEL_3</p>
</div>
</div>
</td>
<td class="px-6 py-5">
<p class="text-sm text-on-surface-variant max-w-xs truncate">Critical response team with firewall override capability.</p>
</td>
<td class="px-6 py-5">
<div class="flex items-center gap-2">
<span class="font-label text-sm text-on-surface">5 peers</span>
<div class="flex -space-x-2">
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="security analyst avatar looking professional and focused" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDUorUtdbZJpk5mds-ACHWH2eQnqRI89iDMGUZS0HoSiXaiWZ5x54TxHYY1Ab2CAbEFt7vcmxhjiTEu4PAKEWLTPkuSFe7GVkC0S7b5ohciWnxA1ClyiOpAWyJhMvLGH9wwYzYkBZnBAw_3OQym_Dzz3JUMYRalvV2FzZSkmN2nOmYCG_KqEyT2VH-tnGnm1ODh1MiOTsXXDvFYfe5GGALFFYhInnbon4UL1S6gTvf49kyaZ5LqWX3oA_6OQbnIbIV8LmLMVJLiKXs"/>
<img alt="Member" class="w-6 h-6 rounded-full border-2 border-surface-container" data-alt="woman security expert avatar in dark studio setting" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBPoxA8QCL7aBgWIFRjQIxccTGvVXo6xErWYABA6S82JXXgVawo7IAV3Ea-_bklUcDeRyNty-j88IMhTwFXZCgVWlDDIjQrp-FZ8DuiNO3ZEWhjATiv_sU1EM91y3Hz7blBGja27UDydXBzFe16kIy1SObZkkAeKtfnkbWtE9WrzIYwMiF7a8oYjDB6XXWFYjWAK_tcBYe4uld6uatihkRuKiQlUouOZXXJGwrPajlPGnu-HnnNsT1sQj22h_UZCd3BjmBJojgG2bM"/>
<div class="w-6 h-6 rounded-full border-2 border-surface-container bg-surface-container-highest flex items-center justify-center text-[8px] font-bold text-outline">+3</div>
</div>
</div>
</td>
<td class="px-6 py-5 text-right">
<div class="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-2 rounded-lg text-outline hover:text-tertiary hover:bg-tertiary/10 transition-colors">
<span class="material-symbols-outlined text-xl">group</span>
</button>
<button class="p-2 rounded-lg text-outline hover:text-error hover:bg-error/10 transition-colors">
<span class="material-symbols-outlined text-xl">delete</span>
</button>
</div>
</td>
</tr>
</tbody>
</table>
</div>
<!-- Table Footer/Pagination -->
<div class="px-6 py-4 flex justify-between items-center bg-surface-container-low border-t border-outline-variant/10">
<p class="font-label text-xs text-outline">Showing <span class="text-on-surface">4</span> groups</p>
<div class="flex gap-1">
<button class="p-1 rounded hover:bg-surface-container-highest text-outline disabled:opacity-30" disabled="">
<span class="material-symbols-outlined text-sm">chevron_left</span>
</button>
<button class="w-6 h-6 flex items-center justify-center rounded bg-primary-container text-on-primary-container text-[10px] font-bold">1</button>
<button class="p-1 rounded hover:bg-surface-container-highest text-outline">
<span class="material-symbols-outlined text-sm">chevron_right</span>
</button>
</div>
</div>
</div>
<!-- Info Grid -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
<div class="bg-surface-container-low p-6 rounded-xl border-t border-white/5">
<span class="material-symbols-outlined text-tertiary mb-4" style="font-variation-settings: 'FILL' 1;">info</span>
<h4 class="font-headline font-bold text-on-surface mb-2">Policy Mapping</h4>
<p class="text-sm text-on-surface-variant font-body">Groups are used as source and destination entities in Access Policies. Changes to group membership apply in real-time across the mesh.</p>
</div>
<div class="bg-surface-container-low p-6 rounded-xl border-t border-white/5">
<span class="material-symbols-outlined text-primary-container mb-4" style="font-variation-settings: 'FILL' 1;">sync_alt</span>
<h4 class="font-headline font-bold text-on-surface mb-2">External Sync</h4>
<p class="text-sm text-on-surface-variant font-body">Integrate with OIDC providers or LDAP to automatically populate groups based on organizational departments.</p>
</div>
<div class="bg-surface-container-low p-6 rounded-xl border-t border-white/5">
<span class="material-symbols-outlined text-secondary mb-4" style="font-variation-settings: 'FILL' 1;">shield_with_heart</span>
<h4 class="font-headline font-bold text-on-surface mb-2">Zero Trust Keys</h4>
<p class="text-sm text-on-surface-variant font-body">Each group creates a unique trust domain. Rotating group keys won't affect peers outside the specific group profile.</p>
</div>
</div>
</main>
<!-- BottomNavBar / Status Bar -->
<footer class="fixed bottom-0 right-0 w-[calc(100%-16rem)] h-8 flex justify-end gap-6 px-8 items-center z-50 bg-[#110f2f] border-t border-[#474555]/15">
<div class="flex items-center gap-2 text-[#00daf3] animate-pulse">
<span class="material-symbols-outlined text-xs">database</span>
<span class="font-label font-medium text-[10px] uppercase tracking-widest">DB: Connected</span>
</div>
<div class="flex items-center gap-2 text-[#928ea1] opacity-60">
<span class="material-symbols-outlined text-xs">vpn_lock</span>
<span class="font-label font-medium text-[10px] uppercase tracking-widest">WG: Active</span>
</div>
<div class="h-3 w-px bg-outline-variant/30 ml-2"></div>
<div class="flex items-center gap-1">
<div class="w-1.5 h-1.5 rounded-full bg-tertiary shadow-[0_0_4px_rgba(0,218,243,0.8)]"></div>
<span class="font-label text-[10px] text-on-surface/50 uppercase tracking-widest">System Latency: 12ms</span>
</div>
</footer>
</body></html>

<!-- Settings -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;family=Space+Grotesk:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          colors: {
            "surface-container-low": "#191838",
            "surface-container-highest": "#333152",
            "on-background": "#e3dfff",
            "surface-dim": "#110f2f",
            "tertiary-fixed-dim": "#00daf3",
            "surface-tint": "#c7bfff",
            "surface": "#110f2f",
            "surface-container": "#1d1c3c",
            "primary-fixed-dim": "#c7bfff",
            "on-tertiary-container": "#b8f4ff",
            "on-tertiary-fixed": "#001f24",
            "on-primary-fixed-variant": "#3e15d2",
            "primary": "#c7bfff",
            "surface-container-lowest": "#0c092a",
            "outline": "#928ea1",
            "on-primary-fixed": "#170065",
            "surface-bright": "#373557",
            "tertiary-fixed": "#9cf0ff",
            "on-surface-variant": "#c8c4d8",
            "outline-variant": "#474555",
            "primary-container": "#624af4",
            "inverse-on-surface": "#2e2d4e",
            "on-secondary": "#2e2e49",
            "secondary": "#c5c3e5",
            "primary-fixed": "#e4dfff",
            "background": "#110f2f",
            "secondary-fixed": "#e2dfff",
            "tertiary": "#00daf3",
            "tertiary-container": "#007482",
            "on-secondary-fixed-variant": "#444460",
            "error-container": "#93000a",
            "surface-container-high": "#282647",
            "on-tertiary-fixed-variant": "#004f58",
            "on-primary-container": "#ebe6ff",
            "on-primary": "#29009f",
            "on-tertiary": "#00363d",
            "surface-variant": "#333152",
            "secondary-fixed-dim": "#c5c3e5",
            "inverse-primary": "#573de9",
            "secondary-container": "#474663",
            "on-error-container": "#ffdad6",
            "inverse-surface": "#e3dfff",
            "on-secondary-fixed": "#191933",
            "on-secondary-container": "#b7b5d7",
            "on-error": "#690005",
            "on-surface": "#e3dfff",
            "error": "#ffb4ab"
          },
          fontFamily: {
            "headline": ["Inter"],
            "body": ["Inter"],
            "label": ["Space Grotesk"]
          },
          borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
        },
      },
    }
  </script>
<style>
    .material-symbols-outlined {
      font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    .glass-card {
      background: rgba(40, 38, 71, 0.6);
      backdrop-filter: blur(12px);
      border-top: 1px solid rgba(71, 69, 85, 0.15);
    }
    .custom-scrollbar::-webkit-scrollbar {
      width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: #474555;
      border-radius: 10px;
    }
  </style>
</head>
<body class="bg-surface text-on-surface font-body selection:bg-primary-container selection:text-on-primary-container">
<!-- SideNavBar Shell -->
<aside class="fixed left-0 top-0 h-full flex flex-col py-6 bg-[#1d1c3c] dark:bg-[#1d1c3c] h-screen w-64 border-r border-[#474555]/15 z-50">
<div class="px-6 mb-10">
<h1 class="text-2xl font-black tracking-tighter text-[#624af4]">NetLoom</h1>
<p class="font-label text-xs uppercase tracking-widest text-outline mt-1">Network Orchestrator</p>
</div>
<nav class="flex-1 space-y-1 px-3">
<a class="flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out hover:bg-[#282647] text-[#928ea1] hover:text-[#e3dfff] rounded-lg" href="#">
<span class="material-symbols-outlined">dashboard</span>
<span class="font-label text-xs uppercase tracking-wider">Dashboard</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out hover:bg-[#282647] text-[#928ea1] hover:text-[#e3dfff] rounded-lg" href="#">
<span class="material-symbols-outlined">hub</span>
<span class="font-label text-xs uppercase tracking-wider">Peers</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out hover:bg-[#282647] text-[#928ea1] hover:text-[#e3dfff] rounded-lg" href="#">
<span class="material-symbols-outlined">lan</span>
<span class="font-label text-xs uppercase tracking-wider">Networks</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out hover:bg-[#282647] text-[#928ea1] hover:text-[#e3dfff] rounded-lg" href="#">
<span class="material-symbols-outlined">security</span>
<span class="font-label text-xs uppercase tracking-wider">Zones</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out hover:bg-[#282647] text-[#928ea1] hover:text-[#e3dfff] rounded-lg" href="#">
<span class="material-symbols-outlined">group</span>
<span class="font-label text-xs uppercase tracking-wider">Groups</span>
</a>
<a class="flex items-center gap-3 px-4 py-3 transition-all duration-200 ease-in-out hover:bg-[#282647] text-[#928ea1] hover:text-[#e3dfff] rounded-lg" href="#">
<span class="material-symbols-outlined">policy</span>
<span class="font-label text-xs uppercase tracking-wider">Policies</span>
</a>
<!-- ACTIVE: System/Settings -->
<a class="flex items-center gap-3 px-4 py-3 text-[#624af4] font-bold border-r-2 border-[#624af4] bg-[#282647] rounded-l-lg scale-95 duration-150" href="#">
<span class="material-symbols-outlined">settings</span>
<span class="font-label text-xs uppercase tracking-wider">System</span>
</a>
</nav>
<div class="px-6 mt-auto">
<button class="w-full py-3 rounded-lg bg-primary-container text-on-primary-container font-bold text-sm flex items-center justify-center gap-2 hover:opacity-90 transition-opacity">
<span class="material-symbols-outlined text-sm">rocket_launch</span>
        Deploy Config
      </button>
<div class="flex items-center gap-3 mt-8 p-2 rounded-xl bg-surface-container-low border border-outline-variant/10">
<img alt="Admin Profile" class="w-8 h-8 rounded-full bg-surface-container-highest" data-alt="Portrait of a professional network administrator in a modern high-tech office environment, soft neon lighting" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCKJQWVdO3Nju4O_-PGZkuw2f4qPQiFsgD_qZCG3ilb6SHYYMZU7TSHR7MIbh91EbEZW7Z5rhBeNPcRWmhkyOyamZYpFvc4x2oGHJTF1nSj_RgiU5MWVDH_LFTl4Z52vZZ9vM4bF9IQQuWJuVd429y47RaLvFdqhDvnXWVI9dd65ef5nRI-0HYoIE8a0v5jm9j80lU44uw4kW_hC767zJnjg4Xzx1wz9pVcxyLDk2xegJJzDhCZzkku2lNpQEMwT_2rr-pGGyj3akQ"/>
<div class="overflow-hidden">
<p class="text-xs font-bold truncate">Admin User</p>
<p class="text-[10px] text-outline truncate">Root Access</p>
</div>
</div>
</div>
</aside>
<!-- TopAppBar Shell -->
<header class="fixed top-0 right-0 h-16 bg-[#110f2f]/80 backdrop-blur-md flex justify-between items-center w-full px-8 ml-64 max-w-[calc(100%-16rem)] z-40 border-b border-[#474555]/15">
<div class="flex items-center gap-4 w-1/3">
<div class="relative w-full max-w-xs group">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
<input class="w-full bg-surface-container-low border-none rounded-full py-2 pl-10 pr-4 text-sm focus:ring-1 focus:ring-primary-container transition-all placeholder:text-outline/50" placeholder="Search system settings..." type="text"/>
</div>
</div>
<div class="flex items-center gap-6">
<button class="text-[#928ea1] hover:text-[#ff8600] transition-colors relative">
<span class="material-symbols-outlined">notifications</span>
<span class="absolute top-0 right-0 w-2 h-2 bg-tertiary rounded-full shadow-[0_0_8px_#00daf3]"></span>
</button>
<button class="text-[#928ea1] hover:text-[#ff8600] transition-colors">
<span class="material-symbols-outlined">settings_input_component</span>
</button>
<button class="text-[#928ea1] hover:text-[#ff8600] transition-colors">
<span class="material-symbols-outlined">account_circle</span>
</button>
</div>
</header>
<!-- Main Canvas -->
<main class="ml-64 pt-24 pb-16 px-12 min-h-screen bg-surface">
<div class="max-w-5xl mx-auto">
<!-- Editorial Header -->
<div class="mb-12">
<h2 class="text-4xl font-black tracking-tight font-headline text-on-surface mb-2">System Settings</h2>
<p class="text-outline max-w-2xl font-body">Orchestrate your network environment. Adjust global configurations, security protocols, and integration webhooks from a single pane of glass.</p>
</div>
<!-- Settings Tabs -->
<div class="flex gap-8 border-b border-outline-variant/15 mb-10 overflow-x-auto custom-scrollbar">
<button class="pb-4 text-sm font-bold text-primary border-b-2 border-primary flex items-center gap-2 whitespace-nowrap">
<span class="material-symbols-outlined text-lg">tune</span>
          General
        </button>
<button class="pb-4 text-sm font-medium text-outline hover:text-tertiary transition-colors flex items-center gap-2 whitespace-nowrap">
<span class="material-symbols-outlined text-lg">shield</span>
          Security
        </button>
<button class="pb-4 text-sm font-medium text-outline hover:text-tertiary transition-colors flex items-center gap-2 whitespace-nowrap">
<span class="material-symbols-outlined text-lg">webhook</span>
          Webhooks
        </button>
<button class="pb-4 text-sm font-medium text-outline hover:text-tertiary transition-colors flex items-center gap-2 whitespace-nowrap">
<span class="material-symbols-outlined text-lg">settings_ethernet</span>
          Advanced
        </button>
</div>
<!-- Bento Grid Layout for Settings Sections -->
<div class="grid grid-cols-12 gap-8">
<!-- Server Configuration Section -->
<section class="col-span-12 lg:col-span-8 space-y-8">
<div class="glass-card p-8 rounded-xl border-l-4 border-primary-container shadow-2xl shadow-black/20">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center justify-center text-primary-container">
<span class="material-symbols-outlined">dns</span>
</div>
<div>
<h3 class="text-xl font-bold font-headline">Server Configuration</h3>
<p class="text-xs text-outline font-label uppercase tracking-widest mt-0.5">Core Interface Parameters</p>
</div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
<div class="space-y-2">
<label class="font-label text-xs uppercase tracking-widest text-outline ml-1">Interface Name</label>
<input class="w-full bg-surface-container-highest border-none rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary-container/50 font-label" type="text" value="loom-tun0"/>
</div>
<div class="space-y-2">
<label class="font-label text-xs uppercase tracking-widest text-outline ml-1">Listen Port</label>
<input class="w-full bg-surface-container-highest border-none rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary-container/50 font-label" type="number" value="51820"/>
</div>
<div class="md:col-span-2 space-y-2">
<label class="font-label text-xs uppercase tracking-widest text-outline ml-1">Public Key</label>
<div class="flex gap-2">
<div class="flex-1 bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3 text-xs font-label text-tertiary tracking-tight flex items-center overflow-hidden italic">
<span class="truncate">G9kYV_mP9u2L-z8xQ5rR_wV1nS0eT4aY7cM3bF6hJ9o=</span>
</div>
<button class="bg-surface-container-highest hover:bg-surface-bright text-on-surface-variant p-3 rounded-lg transition-colors flex items-center justify-center">
<span class="material-symbols-outlined text-lg">content_copy</span>
</button>
</div>
</div>
</div>
<div class="mt-8 pt-8 border-t border-outline-variant/10 flex justify-end">
<button class="px-6 py-2.5 rounded-lg bg-surface-container-highest text-on-surface text-sm font-semibold hover:bg-surface-bright transition-all">
                Rotate Keys
              </button>
</div>
</div>
<!-- Network Defaults -->
<div class="glass-card p-8 rounded-xl shadow-2xl shadow-black/20">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-tertiary-container/10 flex items-center justify-center text-tertiary">
<span class="material-symbols-outlined">settings_input_antenna</span>
</div>
<div>
<h3 class="text-xl font-bold font-headline">Network Defaults</h3>
<p class="text-xs text-outline font-label uppercase tracking-widest mt-0.5">Automated Traffic Handling</p>
</div>
</div>
<div class="space-y-6">
<!-- Toggle 1 -->
<div class="flex items-center justify-between p-4 rounded-lg hover:bg-surface-container-high transition-colors">
<div>
<p class="text-sm font-bold">Auto-Assign Peer IPs</p>
<p class="text-xs text-outline mt-1">Automatically allocate next available IP in defined subnet</p>
</div>
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-container"></div>
</label>
</div>
<!-- Toggle 2 -->
<div class="flex items-center justify-between p-4 rounded-lg hover:bg-surface-container-high transition-colors">
<div>
<p class="text-sm font-bold">Persistent Keepalive</p>
<p class="text-xs text-outline mt-1">Maintain connection state through NAT firewalls</p>
</div>
<div class="flex items-center gap-3">
<span class="font-label text-xs text-outline">25 SEC</span>
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-container"></div>
</label>
</div>
</div>
<!-- Toggle 3 -->
<div class="flex items-center justify-between p-4 rounded-lg hover:bg-surface-container-high transition-colors">
<div>
<p class="text-sm font-bold">Global DNS Routing</p>
<p class="text-xs text-outline mt-1">Force all peer traffic through system DNS resolvers</p>
</div>
<label class="relative inline-flex items-center cursor-pointer">
<input class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-container"></div>
</label>
</div>
</div>
</div>
</section>
<!-- Right Side: Status and Quick Actions -->
<aside class="col-span-12 lg:col-span-4 space-y-8">
<!-- Status Insight -->
<div class="bg-surface-container p-6 rounded-xl border border-outline-variant/10">
<h4 class="font-label text-[10px] uppercase tracking-[0.2em] text-outline mb-6">Orchestration Health</h4>
<div class="space-y-4">
<div class="flex justify-between items-center">
<span class="text-sm text-on-surface-variant">Active Instances</span>
<span class="font-label text-sm text-on-surface font-bold">14 / 20</span>
</div>
<div class="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden">
<div class="bg-primary-container h-full w-[70%]"></div>
</div>
<div class="flex justify-between items-center pt-4">
<span class="text-sm text-on-surface-variant">Sync Status</span>
<div class="flex items-center gap-2">
<span class="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_#00daf3]"></span>
<span class="text-sm text-tertiary font-bold">In-Sync</span>
</div>
</div>
</div>
</div>
<!-- Documentation Callout -->
<div class="relative group overflow-hidden rounded-xl aspect-square bg-surface-container-highest">
<img alt="Documentation Art" class="absolute inset-0 w-full h-full object-cover opacity-30 group-hover:scale-105 transition-transform duration-500" data-alt="Futuristic glowing circuit patterns in deep indigo and neon violet colors, cinematic lighting, ultra-detailed technical aesthetic" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB7PxPGOqO7mmP86uiGdvbzTtKLd6ADpqB5wsqKMFgh9769XENJlzjLq0w4FAwmNXcoaS8bYmdZjZy647acwfpDYdTRH-J2IOBQhvr4C07KWsgEwwcGHyir-FgKZTB11R4AAgueTZ6Ywf-Pd7zZt4vlQMdrmac62NgC6wnkREpHsFhXbAjvs2uT-MfQjCsfil3aRBe06FMvYbwHX4LzxcEx2rpkD8R7CajYclNVhunMINWkIa2mO0tgyMoJZAMcZQJZqNewK269yAI"/>
<div class="absolute inset-0 bg-gradient-to-t from-surface-dim via-transparent to-transparent"></div>
<div class="absolute bottom-0 left-0 p-6">
<p class="font-label text-[10px] uppercase tracking-widest text-primary mb-2">Knowledge Base</p>
<h5 class="text-lg font-bold leading-tight mb-4">Mastering NetLoom Configurations</h5>
<button class="flex items-center gap-2 text-sm font-bold text-on-surface group/btn">
                View Docs 
                <span class="material-symbols-outlined text-sm group-hover/btn:translate-x-1 transition-transform">arrow_forward</span>
</button>
</div>
</div>
<!-- Quick Action -->
<button class="w-full py-4 rounded-xl border border-error/20 bg-error/5 text-error font-bold text-sm flex items-center justify-center gap-2 hover:bg-error hover:text-white transition-all group">
<span class="material-symbols-outlined text-xl">delete_forever</span>
            Wipe Node Configuration
          </button>
</aside>
</div>
<!-- Sticky Footer Actions -->
<div class="fixed bottom-16 right-12 flex gap-4">
<button class="px-8 py-4 rounded-xl bg-surface-bright text-on-surface font-bold shadow-2xl hover:bg-white/10 transition-all">
          Discard
        </button>
<button class="px-8 py-4 rounded-xl bg-gradient-to-br from-[#624af4] to-[#ff8600] text-on-primary-container font-black shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all">
          Commit Changes
        </button>
</div>
</div>
</main>
<!-- BottomNavBar Shell -->
<footer class="fixed bottom-0 left-64 right-0 z-50 flex justify-start items-center px-8 gap-12 bg-[#110f2f] h-10 border-t border-[#474555]/15">
<div class="flex items-center gap-2 text-[#ff8600]">
<span class="material-symbols-outlined text-sm">sensors</span>
<span class="font-label text-[10px] tracking-widest uppercase">System Health</span>
</div>
<div class="flex items-center gap-2 text-[#928ea1]">
<span class="material-symbols-outlined text-sm">timer</span>
<span class="font-label text-[10px] tracking-widest uppercase">Uptime: 99.9%</span>
</div>
<div class="flex items-center gap-2 text-[#928ea1]">
<span class="material-symbols-outlined text-sm">speed</span>
<span class="font-label text-[10px] tracking-widest uppercase">Latency: 12ms</span>
</div>
<div class="flex items-center gap-2 text-[#928ea1]">
<span class="material-symbols-outlined text-sm">verified_user</span>
<span class="font-label text-[10px] tracking-widest uppercase">Secure</span>
</div>
<div class="ml-auto flex items-center gap-2">
<span class="w-2 h-2 rounded-full bg-tertiary"></span>
<span class="font-label text-[10px] tracking-widest uppercase text-on-surface-variant">Live v2.4.1</span>
</div>
</footer>
</body></html>