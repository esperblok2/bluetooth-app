package com.esperblok.btscanner.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import com.esperblok.btscanner.MainActivity
import com.esperblok.btscanner.R
import com.esperblok.btscanner.UpdateManager

class UpdateFragment : Fragment() {

    private lateinit var updateManager: UpdateManager
    private var currentVersion = "1.0"

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        return inflater.inflate(R.layout.fragment_update, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        updateManager = (activity as MainActivity).updateManager
        currentVersion = updateManager.let {
            try {
                requireContext().packageManager.getPackageInfo(requireContext().packageName, 0).versionName ?: "1.0"
            } catch (e: Exception) {
                "1.0"
            }
        }

        val tvCurrent = view.findViewById<TextView>(R.id.tv_current_version)
        val tvLatest = view.findViewById<TextView>(R.id.tv_latest_version)
        val tvStatus = view.findViewById<TextView>(R.id.tv_update_status)
        val btnCheck = view.findViewById<Button>(R.id.btn_check_update)
        val btnDownload = view.findViewById<Button>(R.id.btn_download)
        val progressBar = view.findViewById<ProgressBar>(R.id.progress_update)

        tvCurrent.text = "Huidige versie: $currentVersion"
        btnDownload.visibility = View.GONE
        progressBar.visibility = View.GONE

        btnCheck.setOnClickListener {
            progressBar.visibility = View.VISIBLE
            tvStatus.text = "Controleren op updates..."
            btnCheck.isEnabled = false

            updateManager.checkForUpdates { hasUpdate, latestVersion, changelog ->
                activity?.runOnUiThread {
                    tvLatest.text = "Laatste versie: $latestVersion"
                    progressBar.visibility = View.GONE
                    btnCheck.isEnabled = true

                    if (hasUpdate) {
                        tvStatus.text = "Update beschikbaar: v$latestVersion"
                        btnDownload.visibility = View.VISIBLE
                        btnDownload.setOnClickListener {
                            showInstallDialog(latestVersion, changelog)
                        }
                    } else {
                        tvStatus.text = "Je hebt de laatste versie!"
                        btnDownload.visibility = View.GONE
                    }
                }
            }
        }
    }

    private fun showInstallDialog(version: String, changelog: String) {
        AlertDialog.Builder(requireContext())
            .setTitle("Update beschikbaar: v$version")
            .setMessage(buildString {
                appendLine("Wil je de update downloaden en installeren?")
                if (changelog.isNotEmpty()) {
                    appendLine()
                    appendLine("Wat is er nieuw:")
                    appendLine(changelog)
                }
            })
            .setPositiveButton("Download & Installeer") { _, _ ->
                updateManager.downloadAndInstall()
            }
            .setNegativeButton("Annuleren", null)
            .show()
    }
}
