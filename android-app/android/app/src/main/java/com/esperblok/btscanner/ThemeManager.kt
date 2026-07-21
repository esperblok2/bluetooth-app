package com.esperblok.btscanner

import android.app.Activity
import android.content.Context
import android.content.SharedPreferences
import android.graphics.Color
import android.view.View
import android.view.Window
import androidx.core.view.WindowCompat

data class Theme(
    val name: String,
    val accent: Int,
    val accent2: Int,
    val accent3: Int
)

object ThemeManager {

    val themes = mapOf(
        "Blauw" to Theme("Blauw", Color.parseColor("#00D4FF"), Color.parseColor("#0099CC"), Color.parseColor("#006699")),
        "Roze" to Theme("Roze", Color.parseColor("#FF69B4"), Color.parseColor("#CC4499"), Color.parseColor("#992266")),
        "Groen" to Theme("Groen", Color.parseColor("#00FF88"), Color.parseColor("#00CC66"), Color.parseColor("#009944")),
        "Cyber Paars" to Theme("Cyber Paars", Color.parseColor("#BB86FC"), Color.parseColor("#9966CC"), Color.parseColor("#774499")),
        "Zonsondergang" to Theme("Zonsondergang", Color.parseColor("#FF6B35"), Color.parseColor("#CC5522"), Color.parseColor("#993311"))
    )

    const val BG = 0xFF0A0A1A.toInt()
    const val CARD = 0xFF161B22.toInt()
    const val BORDER = 0xFF21262D.toInt()
    const val GREEN = 0xFF00FF88.toInt()
    const val YELLOW = 0xFFFFCC00.toInt()
    const val RED = 0xFFFF4466.toInt()
    const val TEXT = 0xFFE6EDF3.toInt()
    const val DIM = 0xFF7D8590.toInt()
    const val NAV_BG = 0xFF0D1117.toInt()

    private var currentThemeName = "Blauw"

    fun getCurrentTheme(): Theme = themes[currentThemeName] ?: themes["Blauw"]!!

    fun getThemeNames(): List<String> = themes.keys.toList()

    fun setTheme(name: String) {
        currentThemeName = name
    }

    fun applyTheme(activity: Activity) {
        val window = activity.window
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = BG
        window.navigationBarColor = NAV_BG
    }

    fun saveTheme(context: Context, name: String) {
        currentThemeName = name
        getPrefs(context).edit().putString("theme", name).apply()
    }

    fun loadTheme(context: Context) {
        currentThemeName = getPrefs(context).getString("theme", "Blauw") ?: "Blauw"
    }

    private fun getPrefs(context: Context): SharedPreferences =
        context.getSharedPreferences("bt_theme", Context.MODE_PRIVATE)
}
