package com.esperblok.btscanner

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.fragments.*
import com.google.android.material.bottomnavigation.BottomNavigationView

class MainActivity : AppCompatActivity() {

    lateinit var bluetoothHelper: BluetoothHelper
    lateinit var securityManager: SecurityManager
    lateinit var hidHelper: HidHelper
    lateinit var deviceNotesManager: DeviceNotesManager
    lateinit var updateManager: UpdateManager

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        if (results.values.all { it }) {
            bluetoothHelper.loadPairedDevices()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ThemeManager.loadTheme(this)
        setContentView(R.layout.activity_main)
        ThemeManager.applyTheme(this)

        bluetoothHelper = BluetoothHelper(this)
        securityManager = SecurityManager(this)
        hidHelper = HidHelper(this)
        deviceNotesManager = DeviceNotesManager(this)
        updateManager = UpdateManager(this)

        bluetoothHelper.registerReceiver()
        requestBluetoothPermissions()
        checkForUpdates()

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

    private fun checkForUpdates() {
        val currentVersion = try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: "1.0"
        } catch (e: Exception) {
            "1.0"
        }
        updateManager.setCurrentVersion(currentVersion)

        updateManager.checkForUpdates { hasUpdate, latestVersion, changelog ->
            if (hasUpdate) {
                runOnUiThread {
                    AlertDialog.Builder(this)
                        .setTitle("Update beschikbaar: v$latestVersion")
                        .setMessage(buildString {
                            appendLine("Er is een nieuwe versie beschikbaar!")
                            if (changelog.isNotEmpty()) {
                                appendLine()
                                appendLine("Wat is er nieuw:")
                                appendLine(changelog)
                            }
                            appendLine()
                            appendLine("Automatisch downloaden en installeren?")
                        })
                        .setPositiveButton("Ja, update!") { _, _ ->
                            updateManager.downloadAndInstall()
                        }
                        .setNegativeButton("Later") { dialog, _ ->
                            dialog.dismiss()
                        }
                        .setCancelable(false)
                        .show()
                }
            }
        }
    }

    private fun requestBluetoothPermissions() {
        val perms = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
            perms.add(Manifest.permission.BLUETOOTH_SCAN)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            perms.add(Manifest.permission.BLUETOOTH_CONNECT)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            perms.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        if (perms.isNotEmpty()) {
            permissionLauncher.launch(perms.toTypedArray())
        } else {
            bluetoothHelper.loadPairedDevices()
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
        updateManager.cancelUpdate()
    }
}
