package com.esperblok.btscanner

import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.fragments.*
import com.google.android.material.bottomnavigation.BottomNavigationView

class MainActivity : AppCompatActivity() {

    lateinit var bluetoothHelper: BluetoothHelper
    lateinit var securityManager: SecurityManager
    lateinit var hidHelper: HidHelper
    lateinit var deviceNotesManager: DeviceNotesManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ThemeManager.loadTheme(this)
        setContentView(R.layout.activity_main)
        ThemeManager.applyTheme(this)

        bluetoothHelper = BluetoothHelper(this)
        securityManager = SecurityManager(this)
        hidHelper = HidHelper(this)
        deviceNotesManager = DeviceNotesManager(this)

        bluetoothHelper.registerReceiver()

        val bottomNav = findViewById<BottomNavigationView>(R.id.bottom_nav)

        if (savedInstanceState == null) {
            loadFragment(ScanFragment())
        }

        bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_scan -> { loadFragment(ScanFragment()); true }
                R.id.nav_control -> { loadFragment(ControlFragment()); true }
                R.id.nav_info -> { loadFragment(InfoFragment()); true }
                R.id.nav_security -> { loadFragment(SecurityFragment()); true }
                R.id.nav_update -> { loadFragment(UpdateFragment()); true }
                else -> false
            }
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(0, 1001, 0, "Thema Wisselen")
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == 1001) {
            showThemePicker()
            return true
        }
        return super.onOptionsItemSelected(item)
    }

    private fun showThemePicker() {
        val names = ThemeManager.getThemeNames().toTypedArray()
        val current = ThemeManager.getCurrentTheme().name
        val checkedIndex = names.indexOf(current)

        AlertDialog.Builder(this)
            .setTitle("Kies een thema")
            .setSingleChoiceItems(names, checkedIndex) { dialog, which ->
                val selected = names[which]
                ThemeManager.saveTheme(this, selected)
                ThemeManager.setTheme(selected)
                dialog.dismiss()
                recreate()
            }
            .setNegativeButton("Annuleren", null)
            .show()
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, fragment)
            .commit()
    }

    override fun onDestroy() {
        super.onDestroy()
        bluetoothHelper.stopScan()
        bluetoothHelper.unregisterReceiver()
        hidHelper.disconnect()
    }
}
