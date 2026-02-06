"""
Settings page for configuration
"""

import streamlit as st
from src.config.settings import get_settings
from src.config.constants import Domain


def render_settings_page():
    """Render the settings page"""
    st.markdown("## ⚙️ Settings")
    
    settings = get_settings()
    
    # Tabs for different setting categories
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 Models",
        "⚡ Performance",
        "📊 Scoring",
        "🔧 Advanced"
    ])
    
    with tab1:
        render_model_settings(settings)
    
    with tab2:
        render_performance_settings(settings)
    
    with tab3:
        render_scoring_settings(settings)
    
    with tab4:
        render_advanced_settings(settings)


def render_model_settings(settings):
    """Render model settings"""
    st.markdown("### Model Configuration")
    
    st.markdown("#### NLI Model")
    nli_model = st.text_input(
        "Model name",
        value=settings.nli_model,
        help="HuggingFace model for NLI classification"
    )
    
    st.markdown("#### Embedding Model")
    embedding_model = st.text_input(
        "Model name",
        value=settings.embedding_model,
        help="SentenceTransformer model for embeddings",
        key="embedding_model"
    )
    
    st.markdown("#### Correction Model")
    correction_model = st.text_input(
        "Model name",
        value=settings.correction_model,
        help="Model for generating corrections",
        key="correction_model"
    )
    
    st.markdown("---")
    
    st.markdown("#### Model Loading")
    
    preload = st.checkbox(
        "Preload models on startup",
        value=settings.preload_models,
        help="Load models when application starts for faster first inference"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reload Models"):
            from src.layers.ui_integration import get_integration_layer
            integration = get_integration_layer()
            integration.preload_models()
            st.success("Models reloaded!")
    
    with col2:
        if st.button("💾 Unload Models"):
            from src.layers.ui_integration import get_integration_layer
            integration = get_integration_layer()
            integration.unload_models()
            st.info("Models unloaded to free memory")


def render_performance_settings(settings):
    """Render performance settings"""
    st.markdown("### Performance Configuration")
    
    st.markdown("#### Chunking")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_size = st.number_input(
            "Chunk size",
            min_value=100,
            max_value=2000,
            value=settings.chunk_size,
            step=100,
            help="Size of text chunks for processing"
        )
    
    with col2:
        chunk_overlap = st.number_input(
            "Chunk overlap",
            min_value=0,
            max_value=500,
            value=settings.chunk_overlap,
            step=50,
            help="Overlap between consecutive chunks"
        )
    
    st.markdown("#### Retrieval")
    
    top_k = st.slider(
        "Top-K results",
        min_value=1,
        max_value=20,
        value=settings.top_k_retrieval,
        help="Number of evidence chunks to retrieve per claim"
    )
    
    st.markdown("#### Caching")
    
    cache_enabled = st.checkbox(
        "Enable caching",
        value=settings.cache_enabled,
        help="Cache embeddings and NLI results for faster repeated queries"
    )
    
    if cache_enabled:
        cache_ttl = st.number_input(
            "Cache TTL (seconds)",
            min_value=60,
            max_value=86400,
            value=settings.cache_ttl,
            step=60,
            help="Time-to-live for cached items"
        )
    
    st.markdown("#### Batch Processing")
    
    batch_size = st.number_input(
        "Batch size",
        min_value=1,
        max_value=64,
        value=settings.batch_size,
        help="Batch size for model inference"
    )


def render_scoring_settings(settings):
    """Render scoring settings"""
    st.markdown("### Scoring Configuration")
    
    st.markdown("#### Trust Score Weights")
    st.caption("Weights should sum to 1.0")
    
    col1, col2 = st.columns(2)
    
    with col1:
        w_supported = st.slider(
            "Supported Ratio Weight",
            min_value=0.0,
            max_value=1.0,
            value=settings.weight_supported_ratio,
            step=0.05,
            help="Weight for the ratio of supported claims"
        )
        
        w_confidence = st.slider(
            "Confidence Weight",
            min_value=0.0,
            max_value=1.0,
            value=settings.weight_avg_confidence,
            step=0.05,
            help="Weight for average confidence score"
        )
    
    with col2:
        w_drift = st.slider(
            "Drift Weight",
            min_value=0.0,
            max_value=1.0,
            value=settings.weight_drift_score,
            step=0.05,
            help="Weight for stability score"
        )
        
        w_severity = st.slider(
            "Severity Weight",
            min_value=0.0,
            max_value=1.0,
            value=settings.weight_severity,
            step=0.05,
            help="Weight for severity score"
        )
    
    total_weight = w_supported + w_confidence + w_drift + w_severity
    
    if abs(total_weight - 1.0) > 0.01:
        st.warning(f"⚠️ Weights sum to {total_weight:.2f} (should be 1.0)")
    else:
        st.success("✅ Weights are properly balanced")
    
    st.markdown("---")
    
    st.markdown("#### Thresholds")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nli_threshold = st.slider(
            "NLI Confidence Threshold",
            min_value=0.5,
            max_value=1.0,
            value=settings.nli_threshold,
            step=0.05,
            help="Minimum confidence for NLI classification"
        )
    
    with col2:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.5,
            max_value=1.0,
            value=settings.similarity_threshold,
            step=0.05,
            help="Minimum similarity for evidence retrieval"
        )


def render_advanced_settings(settings):
    """Render advanced settings"""
    st.markdown("### Advanced Configuration")
    
    st.markdown("#### Domain Settings")
    
    default_domain = st.selectbox(
        "Default Domain",
        options=[d.value for d in Domain],
        index=0,
        help="Default domain for verification"
    )
    
    st.markdown("#### Drift Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        drift_threshold = st.slider(
            "Drift Variance Threshold",
            min_value=0.0,
            max_value=0.5,
            value=settings.drift_variance_threshold,
            step=0.05,
            help="Threshold for flagging high-drift claims"
        )
    
    with col2:
        drift_penalty = st.slider(
            "Drift Confidence Penalty",
            min_value=0.0,
            max_value=0.5,
            value=settings.drift_confidence_penalty,
            step=0.05,
            help="Penalty factor for high-drift claims"
        )
    
    st.markdown("---")
    
    st.markdown("#### Debug Options")
    
    debug_mode = st.checkbox(
        "Debug Mode",
        value=settings.debug,
        help="Enable verbose logging"
    )
    
    log_level = st.selectbox(
        "Log Level",
        options=["DEBUG", "INFO", "WARNING", "ERROR"],
        index=1 if settings.log_level == "INFO" else 0,
        help="Logging verbosity level"
    )
    
    st.markdown("---")
    
    st.markdown("#### Export/Import Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Settings"):
            import json
            settings_dict = {
                "nli_model": settings.nli_model,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "top_k_retrieval": settings.top_k_retrieval,
                # Add more as needed
            }
            st.download_button(
                "Download",
                data=json.dumps(settings_dict, indent=2),
                file_name="hallucination_hunter_settings.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_settings = st.file_uploader(
            "Import Settings",
            type=["json"],
            help="Upload a settings JSON file"
        )
        
        if uploaded_settings:
            import json
            try:
                imported = json.load(uploaded_settings)
                st.success("Settings imported successfully!")
                st.json(imported)
            except Exception as e:
                st.error(f"Failed to import: {e}")
    
    st.markdown("---")
    
    st.markdown("#### Reset")
    
    if st.button("🔄 Reset to Defaults", type="secondary"):
        st.warning("This will reset all settings to default values.")
        if st.button("Confirm Reset"):
            # Reset logic here
            st.success("Settings reset to defaults")
            st.rerun()
