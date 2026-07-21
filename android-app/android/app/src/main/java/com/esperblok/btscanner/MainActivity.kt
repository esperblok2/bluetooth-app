package com.esperblok.btscanner

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.fragments.*
import com.google.android.material.bottomnavigation.BottomNavigationView

class MainActivity : AppCompatActivity() {

    lateinit var bluetoothHelper: BluetoothHelper
    lateinit var securityManager: SecurityManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        bluetoothHelper = BluetoothHelper(this)
        securityManager = SecurityManager(this)

        bluetoothHelper.registerReceiver()

        val bottomNav = findViewById<BottomNavigationView>(R.id.bottom_nav)

        if (savedInstanceState == null) {
            loadFragment(ScanFragment())
        }

        bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_scan -> { loadFragment(ScanFragment()); true }
                R.id.nav_paired -> { loadFragment(PairedFragment()); true }
                R.id.nav_control -> { loadFragment(ControlFragment()); true }
                R.id.nav_battery -> { loadFragment(BatteryFragment()); true }
                R.id.nav_local -> { loadFragment(LocalFragment()); true }
                R.id.nav_security -> { loadFragment(SecurityFragment()); true }
                else -> false
            }
        }
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
    }
}
