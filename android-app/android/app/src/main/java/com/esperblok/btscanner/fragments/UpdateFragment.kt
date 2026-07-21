package com.esperblok.btscanner.fragments

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.esperblok.btscanner.R
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL

class UpdateFragment : Fragment() {

    private val GITHUB_URL = "https://raw.githubusercontent.com/esperblok2/bluetooth-app/main/version.json"
    private val APK_URL = "https://github.com/esperblok2/bluetooth-app/raw/main/BT-Scanner-Native.apk"
    private val CURRENT_VERSION = "1.0"

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_update, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val tvVersion = view.findViewById<TextView>(R.id.tv_current_version)
        val tvLatest = view.findViewById<TextView>(R.id.tv_latest_version)
        val tvStatus = view.findViewById<TextView>(R.id.tv_update_status)
        val btnCheck = view.findViewById<Button>(R.id.btn_check_update)
        val btnDownload = view.findViewById<Button>(R.id.btn_download)
        val progressBar = view.findViewById<ProgressBar>(R.id.progress_update)

        tvVersion.text = "Huidige versie: $CURRENT_VERSION"
        btnDownload.visibility = View.GONE
        progressBar.visibility = View.GONE

        btnCheck.setOnClickListener {
            progressBar.visibility = View.VISIBLE
            tvStatus.text = "Controleren op updates..."
            btnCheck.isEnabled = false

            viewLifecycleOwner.lifecycleScope.launch {
                try {
                    val response = withContext(Dispatchers.IO) {
                        URL(GITHUB_URL).readText()
                    }
                    val json = JSONObject(response)
                    val latestVersion = json.optString("version", CURRENT_VERSION)

                    tvLatest.text = "Laatste versie: $latestVersion"
                    progressBar.visibility = View.GONE
                    btnCheck.isEnabled = true

                    if (latestVersion != CURRENT_VERSION) {
                        tvStatus.text = "Update beschikbaar: v$latestVersion"
                        btnDownload.visibility = View.VISIBLE
                    } else {
                        tvStatus.text = "Je hebt de laatste versie!"
                    }
                } catch (e: Exception) {
                    progressBar.visibility = View.GONE
                    btnCheck.isEnabled = true
                    tvStatus.text = "Fout bij controleren: ${e.message}"
                }
            }
        }

        btnDownload.setOnClickListener {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(APK_URL))
            startActivity(intent)
        }
    }
}
