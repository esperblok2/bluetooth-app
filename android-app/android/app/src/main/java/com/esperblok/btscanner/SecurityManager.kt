package com.esperblok.btscanner

import android.content.Context
import android.content.SharedPreferences

class SecurityManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences("bt_security", Context.MODE_PRIVATE)

    var pin: String?
        get() = prefs.getString("pin", null)
        set(value) = prefs.edit().putString("pin", value).apply()

    var isLocked: Boolean
        get() = prefs.getBoolean("is_locked", true)
        set(value) = prefs.edit().putBoolean("is_locked", value).apply()

    var whitelist: MutableSet<String>
        get() = prefs.getStringSet("whitelist", mutableSetOf())?.toMutableSet() ?: mutableSetOf()
        set(value) = prefs.edit().putStringSet("whitelist", value).apply()

    var blocklist: MutableSet<String>
        get() = prefs.getStringSet("blocklist", mutableSetOf())?.toMutableSet() ?: mutableSetOf()
        set(value) = prefs.edit().putStringSet("blocklist", value).apply()

    fun updatePin(newPin: String) {
        pin = newPin
        isLocked = newPin.isNotEmpty()
    }

    fun checkPin(input: String): Boolean {
        if (pin.isNullOrEmpty()) return true
        return pin == input
    }

    fun addToWhitelist(address: String) {
        val set = whitelist
        set.add(address)
        whitelist = set
    }

    fun removeFromWhitelist(address: String) {
        val set = whitelist
        set.remove(address)
        whitelist = set
    }

    fun addToBlocklist(address: String) {
        val set = blocklist
        set.add(address)
        blocklist = set
    }

    fun removeFromBlocklist(address: String) {
        val set = blocklist
        set.remove(address)
        blocklist = set
    }

    fun isBlocked(address: String): Boolean = blocklist.contains(address)

    fun isWhitelisted(address: String): Boolean {
        if (whitelist.isEmpty()) return true
        return whitelist.contains(address)
    }
}
