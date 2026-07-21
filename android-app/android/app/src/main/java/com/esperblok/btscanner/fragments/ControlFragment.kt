package com.esperblok.btscanner.fragments

import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.os.Bundle
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.R

class ControlFragment : Fragment() {

    private lateinit var audioManager: AudioManager

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_control, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        audioManager = requireContext().getSystemService(Context.AUDIO_SERVICE) as AudioManager

        // Media controls
        view.findViewById<Button>(R.id.btn_prev)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_PREVIOUS)
        }
        view.findViewById<Button>(R.id.btn_play)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)
        }
        view.findViewById<Button>(R.id.btn_next)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_NEXT)
        }
        view.findViewById<Button>(R.id.btn_stop)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_MEDIA_STOP)
        }

        // Volume controls
        view.findViewById<Button>(R.id.btn_vol_down)?.setOnClickListener {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, 0)
            Toast.makeText(context, "Volume omlaag", Toast.LENGTH_SHORT).show()
        }
        view.findViewById<Button>(R.id.btn_mute)?.setOnClickListener {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_TOGGLE_MUTE, 0)
            Toast.makeText(context, "Mute aan/uit", Toast.LENGTH_SHORT).show()
        }
        view.findViewById<Button>(R.id.btn_vol_up)?.setOnClickListener {
            audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, 0)
            Toast.makeText(context, "Volume omhoog", Toast.LENGTH_SHORT).show()
        }

        // Keyboard controls
        view.findViewById<Button>(R.id.btn_key_up)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_UP) }
        view.findViewById<Button>(R.id.btn_key_down)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_DOWN) }
        view.findViewById<Button>(R.id.btn_key_left)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_LEFT) }
        view.findViewById<Button>(R.id.btn_key_right)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_DPAD_RIGHT) }
        view.findViewById<Button>(R.id.btn_key_enter)?.setOnClickListener { sendKeyEvent(KeyEvent.KEYCODE_ENTER) }
        view.findViewById<Button>(R.id.btn_key_backspace)?.setOnClickListener {
            sendKeyEvent(KeyEvent.KEYCODE_DEL)
        }

        // Type text
        val etType = view.findViewById<EditText>(R.id.et_type)
        view.findViewById<Button>(R.id.btn_type)?.setOnClickListener {
            val text = etType.text.toString()
            if (text.isNotEmpty()) {
                Toast.makeText(context, "Typen: $text", Toast.LENGTH_SHORT).show()
                etType.text.clear()
                val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
                imm.hideSoftInputFromWindow(etType.windowToken, 0)
            }
        }
    }

    private fun sendKeyEvent(keyCode: Int) {
        val time = System.currentTimeMillis()
        val event = KeyEvent(time, time, KeyEvent.ACTION_DOWN, keyCode, 0)
        audioManager.dispatchMediaKeyEvent(event)
        val upEvent = KeyEvent(time, time, KeyEvent.ACTION_UP, keyCode, 0)
        audioManager.dispatchMediaKeyEvent(upEvent)
    }
}
