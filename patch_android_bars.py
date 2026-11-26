import os
import re
import sys

MARKER = "ASHRAH_SYSTEM_BARS_BRIDGE_V1"

MAIN_ACTIVITY_TEMPLATE = """package {package_name};

import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.FrameLayout;

import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import com.getcapacitor.BridgeActivity;

/* {marker} */
public class MainActivity extends BridgeActivity {{

    private View ashrahStatusBarBg;
    private View ashrahNavBarBg;
    private int currentTopColor = Color.parseColor("#faf2db");
    private int currentBottomColor = Color.parseColor("#f0eadc");
    private boolean currentIsLight = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);

        setupEdgeToEdgeFallbackIfNeeded();
        applyBarColors("#faf2db", "#f0eadc", true);
        attachSystemBarsBridge();
    }}

    @Override
    public void onResume() {{
        super.onResume();
        attachSystemBarsBridge();
        runOnUiThread(() -> {{
            try {{
                if (this.bridge != null && this.bridge.getWebView() != null) {{
                    this.bridge.getWebView().evaluateJavascript(
                        "if (typeof window.syncAshrahSystemBars === 'function') window.syncAshrahSystemBars();",
                        null
                    );
                }}
            }} catch (Exception ignored) {{}}
        }});
    }}

    private void attachSystemBarsBridge() {{
        try {{
            if (this.bridge != null) {{
                WebView webView = this.bridge.getWebView();
                if (webView != null) {{
                    webView.addJavascriptInterface(new AshrahSystemBarsBridge(), "AshrahSystemBars");
                }}
            }}
        }} catch (Exception ignored) {{}}
    }}

    private void setupEdgeToEdgeFallbackIfNeeded() {{
        if (Build.VERSION.SDK_INT < 35) {{
            return;
        }}
        try {{
            final Window window = getWindow();
            if (window == null) return;
            final View decor = window.getDecorView();
            if (!(decor instanceof FrameLayout)) return;
            final FrameLayout decorFrame = (FrameLayout) decor;
            final View contentView = findViewById(android.R.id.content);

            if (ashrahStatusBarBg == null) {{
                ashrahStatusBarBg = new View(this);
                ashrahStatusBarBg.setClickable(false);
                ashrahStatusBarBg.setFocusable(false);
                ashrahStatusBarBg.setBackgroundColor(currentTopColor);
                decorFrame.addView(
                    ashrahStatusBarBg,
                    new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        0,
                        Gravity.TOP
                    )
                );
            }}

            if (ashrahNavBarBg == null) {{
                ashrahNavBarBg = new View(this);
                ashrahNavBarBg.setClickable(false);
                ashrahNavBarBg.setFocusable(false);
                ashrahNavBarBg.setBackgroundColor(currentBottomColor);
                decorFrame.addView(
                    ashrahNavBarBg,
                    new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        0,
                        Gravity.BOTTOM
                    )
                );
            }}

            ViewCompat.setOnApplyWindowInsetsListener(decorFrame, (v, windowInsets) -> {{
                Insets bars = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars());
                if (ashrahStatusBarBg != null) {{
                    ViewGroup.LayoutParams lp = ashrahStatusBarBg.getLayoutParams();
                    if (lp.height != bars.top) {{
                        lp.height = bars.top;
                        ashrahStatusBarBg.setLayoutParams(lp);
                    }}
                }}
                if (ashrahNavBarBg != null) {{
                    ViewGroup.LayoutParams lp = ashrahNavBarBg.getLayoutParams();
                    if (lp.height != bars.bottom) {{
                        lp.height = bars.bottom;
                        ashrahNavBarBg.setLayoutParams(lp);
                    }}
                }}
                if (contentView != null) {{
                    contentView.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                }}
                return windowInsets;
            }});
            ViewCompat.requestApplyInsets(decorFrame);
        }} catch (Exception ignored) {{}}
    }}

    private int parseHexSafe(String hex, int fallback) {{
        try {{
            if (hex != null && !hex.trim().isEmpty()) {{
                return Color.parseColor(hex.trim());
            }}
        }} catch (Exception ignored) {{}}
        return fallback;
    }}

    private void applyBarColors(final String topHex, final String bottomHex, final boolean isLight) {{
        final int topColor = parseHexSafe(topHex, currentTopColor);
        final int bottomColor = parseHexSafe(bottomHex, currentBottomColor);
        currentTopColor = topColor;
        currentBottomColor = bottomColor;
        currentIsLight = isLight;

        runOnUiThread(() -> {{
            try {{
                Window window = getWindow();
                if (window == null) return;

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {{
                    window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
                    window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_NAVIGATION);
                    window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
                    window.setStatusBarColor(topColor);
                    window.setNavigationBarColor(bottomColor);
                }}

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {{
                    window.setNavigationBarContrastEnforced(false);
                }}

                View decor = window.getDecorView();
                if (decor != null) {{
                    decor.setBackgroundColor(bottomColor);
                    WindowInsetsControllerCompat controller = WindowCompat.getInsetsController(window, decor);
                    if (controller != null) {{
                        controller.setAppearanceLightStatusBars(isLight);
                        controller.setAppearanceLightNavigationBars(isLight);
                    }}
                }}

                if (ashrahStatusBarBg != null) {{
                    ashrahStatusBarBg.setBackgroundColor(topColor);
                }}
                if (ashrahNavBarBg != null) {{
                    ashrahNavBarBg.setBackgroundColor(bottomColor);
                }}
            }} catch (Exception ignored) {{}}
        }});
    }}

    public class AshrahSystemBarsBridge {{
        @JavascriptInterface
        public void setColors(final String topHex, final String bottomHex, final boolean isLight) {{
            applyBarColors(topHex, bottomHex, isLight);
        }}
    }}
}}
"""


def find_main_activity(root_dir):
    java_root = os.path.join(root_dir, "android", "app", "src", "main", "java")
    if not os.path.isdir(java_root):
        return None
    for dirpath, _, filenames in os.walk(java_root):
        if "MainActivity.java" in filenames:
            return os.path.join(dirpath, "MainActivity.java")
    return None


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    main_activity_path = find_main_activity(root_dir)
    if not main_activity_path:
        print("❌ لم يتم العثور على MainActivity.java داخل android/app/src/main/java")
        sys.exit(1)

    with open(main_activity_path, "r", encoding="utf-8") as f:
        content = f.read()

    if MARKER in content:
        print(f"ℹ️ جسر تلوين أشرطة النظام مثبّت بالفعل في: {main_activity_path}")
        return

    pkg_match = re.search(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;", content, re.MULTILINE)
    if not pkg_match:
        print("❌ تعذر استخراج اسم الحزمة (package) من MainActivity.java")
        sys.exit(1)

    package_name = pkg_match.group(1)
    patched = MAIN_ACTIVITY_TEMPLATE.format(package_name=package_name, marker=MARKER)

    with open(main_activity_path, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"✅ تم حقن جسر AshrahSystemBars بنجاح في: {main_activity_path} (package: {package_name})")


if __name__ == "__main__":
    main()
