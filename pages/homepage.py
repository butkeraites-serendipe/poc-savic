import streamlit as st
import re
import base64
from io import BytesIO
from database import (
    save_empresa, get_empresas_by_user, save_endereco_geocoding, get_endereco_geocoding,
    save_avaliacao_cnae, get_avaliacao_cnae,
    get_dominios_nao_corporativos, adicionar_dominio_nao_corporativo, remover_dominio_nao_corporativo,
    get_config_whois_min_days, set_config_whois_min_days
)
from auth import logout_user
from cnpja_api import consultar_cnpj
from google_maps_api import processar_endereco_completo, formatar_endereco_para_geocode
from gemini_api import avaliar_compatibilidade_cnaes


def validate_cnpj(cnpj: str) -> bool:
    """Valida o formato do CNPJ (apenas formato, não dígitos verificadores)."""
    # Remove caracteres não numéricos
    cnpj_clean = re.sub(r'\D', '', cnpj)
    
    # CNPJ deve ter 14 dígitos
    return len(cnpj_clean) == 14


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ para o padrão XX.XXX.XXX/XXXX-XX."""
    cnpj_clean = re.sub(r'\D', '', cnpj)
    
    if len(cnpj_clean) == 14:
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    
    return cnpj


def validate_email(email: str) -> bool:
    """Valida o formato básico do email."""
    if not email:
        return True  # Email é opcional
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def show_homepage():
    """Exibe a homepage com formulário de CNPJ."""
    st.title("🏢 SAVIC - Sistema de Análise de Empresas")
    
    # Barra de logout
    col1, col2 = st.columns([6, 1])
    with col1:
        st.write(f"Bem-vindo, **{st.session_state.username}**!")
    with col2:
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.divider()
    
    # Seção de consulta de dados cadastrais
    st.subheader("🔍 Consultar Dados Cadastrais")
    
    with st.form("consulta_form", clear_on_submit=False):
        cnpj_consulta = st.text_input(
            "CNPJ para Consulta",
            placeholder="00.000.000/0000-00 ou 00000000000000",
            help="Digite o CNPJ da empresa para consultar dados cadastrais na Receita Federal",
            key="cnpj_consulta"
        )
        consultar_button = st.form_submit_button("Consultar CNPJ", use_container_width=True)
        
        if consultar_button:
            if not cnpj_consulta:
                st.error("Por favor, informe o CNPJ para consulta")
            elif not validate_cnpj(cnpj_consulta):
                st.error("CNPJ inválido. O CNPJ deve conter 14 dígitos.")
            else:
                # Verifica se deve forçar atualização
                forcar_atualizacao = st.session_state.get("forcar_atualizacao", False)
                
                with st.spinner("Consultando dados cadastrais..."):
                    try:
                        dados = consultar_cnpj(cnpj_consulta, usar_cache=True, forcar_atualizacao=forcar_atualizacao)
                        
                        if dados:
                            # Armazenar dados no session_state para exibição fora do form
                            st.session_state.consulta_dados = dados
                            st.session_state.consulta_cnpj = cnpj_consulta
                            st.session_state.forcar_atualizacao = False
                            st.rerun()
                    
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro inesperado ao consultar CNPJ: {str(e)}")
    
    # Exibir resultados da consulta (fora do formulário)
    if "consulta_dados" in st.session_state and st.session_state.consulta_dados:
        dados = st.session_state.consulta_dados
        cnpj_consulta = st.session_state.get("consulta_cnpj", "")
        
        # Verifica se veio do cache
        is_cached = dados.get("_cached", False)
        cached_at = dados.get("_cached_at", "")
        
        if is_cached:
            st.success(f"✅ Dados encontrados no cache (consultado em: {cached_at})")
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("🔄 Atualizar da API", use_container_width=True, key="btn_atualizar"):
                    # Força atualização e mantém o CNPJ para nova consulta
                    st.session_state.forcar_atualizacao = True
                    # Remove dados do cache para forçar nova consulta
                    if "consulta_dados" in st.session_state:
                        del st.session_state.consulta_dados
                    # Faz nova consulta automaticamente
                    try:
                        dados = consultar_cnpj(cnpj_consulta, usar_cache=True, forcar_atualizacao=True)
                        if dados:
                            st.session_state.consulta_dados = dados
                            st.session_state.consulta_cnpj = cnpj_consulta
                            st.session_state.forcar_atualizacao = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {str(e)}")
        else:
            st.success("✅ Dados encontrados!")
        
        # Extrair dados da estrutura da API CNPJA
        company = dados.get("company", {})
        tax_id = dados.get("taxId", "")
        company_name = company.get("name", "")
        alias = dados.get("alias")
        status = dados.get("status", {})
        founded = dados.get("founded", "")
        address = dados.get("address", {})
        emails = dados.get("emails", [])
        phones = dados.get("phones", [])
        main_activity = dados.get("mainActivity", {})
        side_activities = dados.get("sideActivities", [])
        
        # Exibir dados principais
        with st.expander("📋 Dados Cadastrais Completos", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if company_name:
                    st.write(f"**Razão Social:** {company_name}")
                if alias:
                    st.write(f"**Nome Fantasia:** {alias}")
                if tax_id:
                    cnpj_formatted = format_cnpj(tax_id)
                    st.write(f"**CNPJ:** {cnpj_formatted}")
                if status:
                    status_text = status.get("text", "N/A") if isinstance(status, dict) else str(status)
                    st.write(f"**Status:** {status_text}")
                if founded:
                    st.write(f"**Data de Abertura:** {founded}")
            
            with col2:
                if emails:
                    email_str = ", ".join([e.get("address", "") for e in emails if isinstance(e, dict)])
                    if email_str:
                        st.write(f"**Email:** {email_str}")
                if phones:
                    phone_str = ", ".join([
                        f"({p.get('area', '')}) {p.get('number', '')}" 
                        for p in phones if isinstance(p, dict)
                    ])
                    if phone_str:
                        st.write(f"**Telefone:** {phone_str}")
            
            # Endereço
            if address and isinstance(address, dict):
                st.divider()
                st.write("**📍 Endereço:**")
                endereco_parts = []
                if address.get("street"):
                    endereco_parts.append(address["street"])
                if address.get("number"):
                    endereco_parts.append(f"nº {address['number']}")
                if address.get("details"):
                    endereco_parts.append(address["details"])
                if address.get("district"):
                    endereco_parts.append(address["district"])
                if address.get("city"):
                    endereco_parts.append(address["city"])
                if address.get("state"):
                    endereco_parts.append(address["state"])
                if address.get("zip"):
                    endereco_parts.append(f"CEP: {address['zip']}")
                
                if endereco_parts:
                    endereco_completo_str = ", ".join(endereco_parts)
                    st.write(endereco_completo_str)
                    
                    # Seção de Geocoding e Imagens
                    cnpj_clean = "".join(filter(str.isdigit, tax_id if tax_id else cnpj_consulta))
                    dados_geocoding = get_endereco_geocoding(cnpj_clean)
                    
                    # Botão para processar geocoding
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button("🗺️ Processar Endereço", use_container_width=True, key="btn_geocode"):
                            with st.spinner("Processando endereço e buscando imagens..."):
                                try:
                                    dados_geocoding = processar_endereco_completo(address)
                                    endereco_formatado = formatar_endereco_para_geocode(address)
                                    save_endereco_geocoding(cnpj_clean, endereco_formatado, dados_geocoding)
                                    st.success("Endereço processado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao processar endereço: {str(e)}")
                    
                    # Exibir dados de geocoding se existirem
                    if dados_geocoding:
                        st.divider()
                        st.write("**🗺️ Informações de Geocoding:**")
                        
                        geocoding = dados_geocoding.get("geocoding", {})
                        if geocoding:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Coordenadas:** {geocoding.get('lat', 'N/A')}, {geocoding.get('lng', 'N/A')}")
                                if geocoding.get("formatted_address"):
                                    st.write(f"**Endereço Formatado:** {geocoding['formatted_address']}")
                            with col2:
                                if geocoding.get("place_id"):
                                    st.write(f"**Place ID:** {geocoding['place_id']}")
                                if dados_geocoding.get("processado_em"):
                                    st.caption(f"Processado em: {dados_geocoding['processado_em']}")
                        
                        # Street View
                        street_view = dados_geocoding.get("street_view", {})
                        street_view_status = street_view.get("status") if street_view else dados_geocoding.get("street_view_status")
                        
                        if street_view_status == "OK":
                            st.write("**📷 Street View:** Disponível")
                            
                            # Exibir imagem Street View
                            street_view_image_bytes = dados_geocoding.get("street_view_image_bytes")
                            if street_view_image_bytes:
                                st.image(street_view_image_bytes, caption="Imagem Street View da fachada", use_container_width=True)
                                
                                # Link para Google Maps
                                if geocoding:
                                    lat = geocoding.get("lat")
                                    lng = geocoding.get("lng")
                                    if lat and lng:
                                        maps_url = f"https://www.google.com/maps?q={lat},{lng}"
                                        st.markdown(f"[🗺️ Ver no Google Maps]({maps_url})")
                        else:
                            st.write("**📷 Street View:** Não disponível para este endereço")
                        
                        # Place Photos
                        place_photos = dados_geocoding.get("place_photos", [])
                        if place_photos and len(place_photos) > 0:
                            st.divider()
                            st.write(f"**📸 Fotos do Local ({len(place_photos)}):**")
                            
                            # Exibir imagens se disponíveis
                            for i, photo in enumerate(place_photos, 1):
                                if photo.get("image_bytes"):
                                    st.image(
                                        photo["image_bytes"],
                                        caption=f"Foto {i} do local ({photo.get('width', 0)}x{photo.get('height', 0)})",
                                        use_container_width=True
                                    )
                                else:
                                    st.write(f"**Foto {i}:**")
                                    st.write(f"- Referência: {photo.get('photo_reference', 'N/A')}")
                                    st.write(f"- Dimensões: {photo.get('width', 0)}x{photo.get('height', 0)}")
                        
                        # Erros se houver
                        erros = dados_geocoding.get("erros", [])
                        if erros:
                            st.warning("⚠️ Alguns erros ocorreram durante o processamento:")
                            for erro in erros:
                                st.write(f"- {erro}")
                        
                        # Seção de Análise de Risco de Endereço (Gemini Vision)
                        if street_view_image_bytes or (place_photos and len(place_photos) > 0):
                            st.divider()
                            st.write("**🔍 Análise de Risco de Endereço (Gemini Vision):**")
                            
                            from address_risk_service import analisar_endereco_completo
                            from database import get_analise_risco_endereco
                            
                            analise_existente = get_analise_risco_endereco(cnpj_clean)
                            
                            col1, col2 = st.columns([3, 1])
                            with col2:
                                if st.button("🤖 Analisar Risco", use_container_width=True, key="btn_analisar_risco"):
                                    with st.spinner("Analisando imagem do endereço com Gemini Vision..."):
                                        try:
                                            # Preparar CNAEs
                                            cnaes = []
                                            if main_activity and isinstance(main_activity, dict):
                                                cnaes.append({
                                                    "codigo": str(main_activity.get("id", "")),
                                                    "descricao": main_activity.get("text", "")
                                                })
                                            if side_activities and isinstance(side_activities, list):
                                                for sec in side_activities:
                                                    if isinstance(sec, dict):
                                                        cnaes.append({
                                                            "codigo": str(sec.get("id", "")),
                                                            "descricao": sec.get("text", "")
                                                        })
                                            
                                            # Usar imagem disponível
                                            image_bytes = street_view_image_bytes
                                            if not image_bytes and place_photos:
                                                image_bytes = place_photos[0].get("image_bytes")
                                            
                                            if image_bytes and cnaes:
                                                resultado = analisar_endereco_completo(
                                                    cnpj=cnpj_clean,
                                                    image_bytes=image_bytes,
                                                    cnaes=cnaes,
                                                    razao_social=company_name,
                                                    nome_fantasia=alias
                                                )
                                                
                                                if resultado.get("erro"):
                                                    st.error(f"Erro na análise: {resultado['erro']}")
                                                else:
                                                    st.success("Análise de risco concluída!")
                                                    st.rerun()
                                            else:
                                                st.error("Imagem ou CNAEs não disponíveis para análise.")
                                        except Exception as e:
                                            st.error(f"Erro ao analisar risco: {str(e)}")
                            
                            # Exibir análise existente
                            if analise_existente:
                                analise_visual = analise_existente.get("analise_visual", {})
                                
                                # Indicador de risco
                                risco_final = analise_existente.get("risco_final", "INDEFINIDO")
                                score_risco = analise_existente.get("score_risco", 0)
                                
                                if risco_final == "ALTO":
                                    st.error(f"🚨 **Risco ALTO** (Score: {score_risco}/100)")
                                elif risco_final == "MEDIO":
                                    st.warning(f"⚠️ **Risco MÉDIO** (Score: {score_risco}/100)")
                                elif risco_final == "BAIXO":
                                    st.success(f"✅ **Risco BAIXO** (Score: {score_risco}/100)")
                                else:
                                    st.info(f"❓ **Risco INDEFINIDO** (Score: {score_risco}/100)")
                                
                                # Detalhes da análise
                                with st.expander("📊 Detalhes da Análise Visual"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Zona Aparente:** {analise_visual.get('zona_aparente', 'N/A')}")
                                        st.write(f"**Tipo de Via:** {analise_visual.get('tipo_via', 'N/A')}")
                                        st.write(f"**Tipo Local Esperado:** {analise_existente.get('tipo_local_esperado', 'N/A')}")
                                    with col2:
                                        st.write(f"**Placas Comerciais:** {'Sim' if analise_visual.get('presenca_placas_comerciais') else 'Não'}")
                                        st.write(f"**Vitrines/Lojas:** {'Sim' if analise_visual.get('presenca_vitrines_ou_lojas') else 'Não'}")
                                        st.write(f"**Casas Residenciais:** {'Sim' if analise_visual.get('presenca_casas_residenciais') else 'Não'}")
                                    
                                    compatibilidade = analise_visual.get("compatibilidade_cnae", "N/A")
                                    st.write(f"**Compatibilidade CNAE:** {compatibilidade}")
                                    
                                    motivos = analise_visual.get("motivos_incompatibilidade", [])
                                    if motivos:
                                        st.write("**Motivos de Incompatibilidade:**")
                                        for motivo in motivos:
                                            st.write(f"- {motivo}")
                                
                                # Flags de risco
                                flags = analise_existente.get("flags_risco", [])
                                if flags:
                                    with st.expander("🏷️ Flags de Risco"):
                                        for flag in flags:
                                            st.write(f"- {flag}")
                                
                                # Análise detalhada
                                analise_detalhada = analise_visual.get("analise_detalhada", "")
                                if analise_detalhada:
                                    with st.expander("📝 Análise Detalhada"):
                                        st.write(analise_detalhada)
                                
                                if analise_existente.get("analisado_em"):
                                    st.caption(f"Análise realizada em: {analise_existente['analisado_em']}")
            
            # Todas as atividades CNAE (Principal + Secundárias)
            st.divider()
            st.write("**📊 Atividades CNAE:**")
            
            # Criar tabela com todas as atividades
            atividades_data = []
            
            # Adiciona atividade principal
            if main_activity and isinstance(main_activity, dict):
                atividades_data.append({
                    "Tipo": "Principal",
                    "Código CNAE": str(main_activity.get("id", "")),
                    "Descrição": main_activity.get("text", "")
                })
            
            # Adiciona atividades secundárias
            if side_activities and isinstance(side_activities, list):
                for atividade in side_activities:
                    if isinstance(atividade, dict):
                        atividades_data.append({
                            "Tipo": "Secundária",
                            "Código CNAE": str(atividade.get("id", "")),
                            "Descrição": atividade.get("text", "")
                        })
            
            # Exibe tabela com todas as atividades
            if atividades_data:
                total = len(atividades_data)
                principal_count = sum(1 for a in atividades_data if a["Tipo"] == "Principal")
                secundarias_count = total - principal_count
                
                if secundarias_count > 0:
                    st.write(f"**Total:** {total} atividades ({principal_count} principal, {secundarias_count} secundárias)")
                else:
                    st.write(f"**Total:** {total} atividade principal")
                
                st.dataframe(atividades_data, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma atividade CNAE encontrada.")
            
            # Seção de Avaliação de Compatibilidade de CNAEs
            if main_activity and isinstance(main_activity, dict):
                st.divider()
                st.write("**🤖 Avaliação de Compatibilidade de CNAEs (Gemini AI):**")
                
                cnpj_clean = "".join(filter(str.isdigit, tax_id if tax_id else cnpj_consulta))
                avaliacao_existente = get_avaliacao_cnae(cnpj_clean)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🔍 Avaliar Compatibilidade", use_container_width=True, key="btn_avaliar_cnae"):
                        with st.spinner("Avaliando compatibilidade dos CNAEs com Gemini AI..."):
                            try:
                                avaliacao = avaliar_compatibilidade_cnaes(
                                    main_activity,
                                    side_activities if side_activities else [],
                                    company_name,
                                    alias
                                )
                                
                                if avaliacao.get("erro"):
                                    st.error(f"Erro: {avaliacao['erro']}")
                                else:
                                    # Salvar avaliação
                                    save_avaliacao_cnae(cnpj_clean, avaliacao)
                                    st.success("Avaliação concluída!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao avaliar CNAEs: {str(e)}")
                
                # Exibir avaliação se existir
                if avaliacao_existente:
                    st.write("**📊 Resultado da Avaliação:**")
                    
                    compativel = avaliacao_existente.get("compativel")
                    score = avaliacao_existente.get("score")
                    
                    if compativel is not None:
                        if compativel:
                            st.success(f"✅ Compatível (Score: {score:.0f}/100)")
                        else:
                            st.error(f"❌ Incompatível (Score: {score:.0f}/100)")
                    elif score is not None:
                        if score >= 70:
                            st.success(f"✅ Score: {score:.0f}/100")
                        elif score >= 50:
                            st.warning(f"⚠️ Score: {score:.0f}/100")
                        else:
                            st.error(f"❌ Score: {score:.0f}/100")
                    
                    if avaliacao_existente.get("analise"):
                        st.write("**Análise:**")
                        st.write(avaliacao_existente["analise"])
                    
                    if avaliacao_existente.get("observacoes"):
                        st.write("**Observações:**")
                        for obs in avaliacao_existente["observacoes"]:
                            st.write(f"- {obs}")
                    
                    if avaliacao_existente.get("avaliado_em"):
                        st.caption(f"Avaliado em: {avaliacao_existente['avaliado_em']}")
            
            # Botão para preencher formulário com dados consultados (fora do form)
            if st.button("💾 Usar estes dados no cadastro", use_container_width=True, key="btn_preencher"):
                cnpj_formatted = format_cnpj(tax_id) if tax_id else format_cnpj(cnpj_consulta)
                email_value = emails[0].get("address", "") if emails and isinstance(emails[0], dict) else ""
                data_abertura_value = founded if founded else ""
                
                st.session_state.prefill_cnpj = cnpj_formatted
                st.session_state.prefill_razao_social = company_name
                st.session_state.prefill_email = email_value
                st.session_state.prefill_data_abertura = data_abertura_value
                
                # Limpar dados da consulta
                if "consulta_dados" in st.session_state:
                    del st.session_state.consulta_dados
                if "consulta_cnpj" in st.session_state:
                    del st.session_state.consulta_cnpj
                
                st.rerun()
        
        # Exibir JSON completo em expander (para debug)
        with st.expander("🔧 Dados JSON Completos (Debug)"):
            st.json(dados)
    
    st.divider()
    
    # Seção de Configuração de Domínios Não Corporativos
    with st.expander("⚙️ Configurar Domínios de Email Não Corporativos"):
        st.write("Gerencie a lista de domínios de email considerados não corporativos (Gmail, Yahoo, etc.)")
        
        dominios = get_dominios_nao_corporativos()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Domínios cadastrados:**")
            if dominios:
                for dominio in dominios:
                    st.write(f"- {dominio}")
            else:
                st.info("Nenhum domínio cadastrado.")
        
        with col2:
            st.write("**Adicionar domínio:**")
            novo_dominio = st.text_input(
                "Domínio (ex: gmail.com)",
                key="novo_dominio",
                placeholder="gmail.com"
            )
            if st.button("➕ Adicionar", key="btn_add_dominio"):
                if novo_dominio:
                    dominio_limpo = novo_dominio.strip().lower()
                    if adicionar_dominio_nao_corporativo(dominio_limpo):
                        st.success(f"Domínio '{dominio_limpo}' adicionado!")
                        st.rerun()
                    else:
                        st.error(f"Domínio '{dominio_limpo}' já existe ou é inválido.")
                else:
                    st.warning("Digite um domínio válido.")
        
        # Remover domínios
        if dominios:
            st.write("**Remover domínio:**")
            dominio_remover = st.selectbox(
                "Selecione o domínio para remover",
                dominios,
                key="select_remover_dominio"
            )
            if st.button("➖ Remover", key="btn_remover_dominio"):
                if remover_dominio_nao_corporativo(dominio_remover):
                    st.success(f"Domínio '{dominio_remover}' removido!")
                    st.rerun()
                else:
                    st.error("Erro ao remover domínio.")
    
    st.divider()
    
    # Seção de Configuração de Limite WHOIS
    with st.expander("⚙️ Configurar Verificação de Idade de Domínio (WHOIS)"):
        st.write("Configure o limite mínimo de dias para considerar um domínio como recente")
        
        min_days_atual = get_config_whois_min_days()
        st.write(f"**Limite atual:** {min_days_atual} dias")
        
        novo_limite = st.number_input(
            "Novo limite (dias)",
            min_value=1,
            max_value=3650,
            value=min_days_atual,
            key="whois_min_days_input"
        )
        
        if st.button("💾 Salvar Limite", key="btn_salvar_whois"):
            if set_config_whois_min_days(int(novo_limite)):
                st.success(f"Limite atualizado para {novo_limite} dias!")
                st.rerun()
            else:
                st.error("Erro ao atualizar limite.")
        
        st.info("💡 Domínios criados há menos dias que o limite serão marcados como recentes.")
    
    st.divider()
    
    # Formulário de CNPJ
    st.subheader("Cadastrar Nova Empresa")
    
    with st.form("cnpj_form", clear_on_submit=True):
        # Preencher campos se houver dados da consulta
        cnpj_prefill = st.session_state.get("prefill_cnpj", "")
        razao_social_prefill = st.session_state.get("prefill_razao_social", "")
        email_prefill = st.session_state.get("prefill_email", "")
        data_abertura_prefill = st.session_state.get("prefill_data_abertura", "")
        
        cnpj = st.text_input(
            "CNPJ",
            value=cnpj_prefill,
            placeholder="00.000.000/0000-00 ou 00000000000000",
            help="Digite o CNPJ da empresa (com ou sem formatação)"
        )
        razao_social = st.text_input(
            "Razão Social (opcional)",
            value=razao_social_prefill,
            placeholder="Nome da empresa",
            help="Nome completo da empresa"
        )
        email = st.text_input(
            "Email (opcional)",
            value=email_prefill,
            placeholder="contato@empresa.com.br",
            help="Email de contato da empresa"
        )
        data_abertura = st.text_input(
            "Data de Abertura (opcional)",
            value=data_abertura_prefill,
            placeholder="YYYY-MM-DD (ex: 2005-03-03)",
            help="Data de abertura da empresa no formato YYYY-MM-DD"
        )
        
        st.divider()
        st.write("**⚠️ Sinalizações de Risco:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            telefone_suspeito = st.checkbox(
                "📞 Número de telefone de contato suspeito",
                help="Marque se o número de telefone fornecido apresenta características suspeitas"
            )
            pressa_aprovacao = st.checkbox(
                "⏰ Pressa em aprovar uma compra ou indício de pouca negociação",
                help="Marque se há indícios de pressa excessiva ou falta de negociação"
            )
        
        with col2:
            entrega_marcada = st.checkbox(
                "📅 Solicitação de entrega dos produtos com hora e dia marcados",
                help="Marque se foi solicitada entrega em horário/dia específico"
            )
            endereco_entrega_diferente = st.checkbox(
                "📍 Informativo de endereço de entrega diferente do endereço de cadastro",
                help="Marque se o endereço de entrega é diferente do endereço cadastrado da empresa"
            )
        
        submit_button = st.form_submit_button("Cadastrar Empresa", use_container_width=True)
        
        if submit_button:
            if not cnpj:
                st.error("Por favor, informe o CNPJ")
            elif not validate_cnpj(cnpj):
                st.error("CNPJ inválido. O CNPJ deve conter 14 dígitos.")
            elif email and not validate_email(email):
                st.error("Email inválido. Por favor, verifique o formato do email.")
            else:
                cnpj_formatted = format_cnpj(cnpj)
                user_id = st.session_state.user_id
                
                success = save_empresa(
                    cnpj_formatted,
                    razao_social if razao_social else None,
                    email if email else None,
                    user_id,
                    data_abertura=data_abertura if data_abertura else None,
                    telefone_suspeito=telefone_suspeito,
                    pressa_aprovacao=pressa_aprovacao,
                    entrega_marcada=entrega_marcada,
                    endereco_entrega_diferente=endereco_entrega_diferente
                )
                
                if success:
                    st.success(f"Empresa cadastrada com sucesso! CNPJ: {cnpj_formatted}")
                    # Limpar dados de preenchimento após cadastro bem-sucedido
                    if "prefill_cnpj" in st.session_state:
                        del st.session_state.prefill_cnpj
                    if "prefill_razao_social" in st.session_state:
                        del st.session_state.prefill_razao_social
                    if "prefill_email" in st.session_state:
                        del st.session_state.prefill_email
                    if "prefill_data_abertura" in st.session_state:
                        del st.session_state.prefill_data_abertura
                else:
                    st.error("Este CNPJ já foi cadastrado anteriormente.")
    
    st.divider()
    
    # Lista de empresas cadastradas
    st.subheader("Empresas Cadastradas")
    
    empresas = get_empresas_by_user(st.session_state.user_id)
    
    if empresas:
        for empresa in empresas:
            with st.container():
                # Verificar se há sinalizações de risco
                sinalizacoes = []
                if empresa.get('email_nao_corporativo'):
                    sinalizacoes.append("📧 Email não corporativo (Gmail, Yahoo, etc.)")
                if empresa.get('email_dominio_diferente'):
                    sinalizacoes.append("📧 Email com domínio diferente do CNPJA")
                if empresa.get('email_dominio_recente'):
                    sinalizacoes.append("🆕 Domínio do email criado recentemente (WHOIS)")
                if empresa.get('telefone_suspeito'):
                    sinalizacoes.append("📞 Telefone suspeito")
                if empresa.get('pressa_aprovacao'):
                    sinalizacoes.append("⏰ Pressa em aprovar")
                if empresa.get('entrega_marcada'):
                    sinalizacoes.append("📅 Entrega marcada")
                if empresa.get('endereco_entrega_diferente'):
                    sinalizacoes.append("📍 Endereço entrega diferente")
                
                tem_sinalizacoes = len(sinalizacoes) > 0
                
                # Header com alerta se houver sinalizações
                if tem_sinalizacoes:
                    st.warning(f"⚠️ **{len(sinalizacoes)} sinalização(ões) de risco**")
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**CNPJ:** {empresa['cnpj']}")
                    if empresa['email']:
                        st.write(f"**Email:** {empresa['email']}")
                    if empresa.get('data_abertura'):
                        st.write(f"**Data de Abertura:** {empresa['data_abertura']}")
                with col2:
                    if empresa['razao_social']:
                        st.write(f"**Razão Social:** {empresa['razao_social']}")
                    else:
                        st.write("*Razão social não informada*")
                with col3:
                    st.caption(f"Cadastrado em: {empresa['created_at']}")
                
                # Exibir sinalizações
                if tem_sinalizacoes:
                    st.write("**Sinalizações:**")
                    for sinalizacao in sinalizacoes:
                        st.write(f"- {sinalizacao}")
                
                st.divider()
    else:
        st.info("Nenhuma empresa cadastrada ainda. Use o formulário acima para cadastrar.")
