package com.esperblok.btscanner

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

data class DeviceNote(
    val address: String,
    val notes: String,
    val name: String = "",
    val lastSeen: Long = System.currentTimeMillis()
)

class DeviceNotesManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences("bt_notes", Context.MODE_PRIVATE)
    private val gson = Gson()

    fun saveNote(note: DeviceNote) {
        val notes = getAllNotes().toMutableMap()
        notes[note.address] = note
        prefs.edit().putString("notes", gson.toJson(notes)).apply()
    }

    fun getNote(address: String): DeviceNote? {
        return getAllNotes()[address]
    }

    fun getAllNotes(): Map<String, DeviceNote> {
        val json = prefs.getString("notes", "{}") ?: "{}"
        val type = object : TypeToken<Map<String, DeviceNote>>() {}.type
        return try {
            gson.fromJson(json, type) ?: emptyMap()
        } catch (e: Exception) {
            emptyMap()
        }
    }

    fun deleteNote(address: String) {
        val notes = getAllNotes().toMutableMap()
        notes.remove(address)
        prefs.edit().putString("notes", gson.toJson(notes)).apply()
    }
}
