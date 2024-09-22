import { makePersisted } from '@solid-primitives/storage'
import axios from 'axios'
import { IoInformationCircleOutline, IoSend } from 'solid-icons/io'
import { For, createSignal } from 'solid-js'
import { SolidMarkdown } from 'solid-markdown'
import { Spinner, SpinnerType } from 'solid-spinner'
import { IAssistantCreateRequest, IAssistantCreateResponse, IKVStoreItem, IResponseMessage, IRunningAssistant, ISettings, IThreadMessage } from './interfaces'
import Swal from 'sweetalert2'
//import Swal from 'sweetalert2'

// @ts-ignore
const BaseURL = window.base_url;
const POST_CREATE = BaseURL + 'create'
const POST_PROCESS = BaseURL + 'process'
const GET_STATUS = BaseURL + 'status/{name}'
const DELETE_ASSISTANT = BaseURL + 'delete/{name}'
const FORCE_DELETE_ASSISTANT = BaseURL + 'delete'

const Settings: ISettings = {
  user: '',
  name: '',
  instructions: '',
  ci: true,
  ciFileURLs: '',
  fs: false,
  vs_name: '',
  fsFileURLs: '',
}

const RunningAssistant: IRunningAssistant = {
  assistant_id: '',
  thread_id: '',
  files: [],
}

function App() {
  const [settings, setSettings] = makePersisted(createSignal<ISettings>(Settings))
  const [runningAssistant, setRunningAssistant] = createSignal<IRunningAssistant>(RunningAssistant)
  const [threadMessages, setThreadMessages] = makePersisted(createSignal<IThreadMessage[]>([]))
  const [prompt, setPrompt] = createSignal<string>('')
  const [processing, setProcessing] = createSignal<boolean>(false)

  const UpdateStatus = async () => {
    if (!processing())
      try {
        const resp = await axios.get<IKVStoreItem[]>(GET_STATUS.replace('{name}', settings().user))
        const data = resp.data
        if (resp.data.length === 0) return
        const assistant_id = data.filter((item) => item.key === 'assistant')[0].value
        const thread_id = data.filter((item) => item.key === 'thread')[0].value
        const files = data.filter((item) => item.key === 'file').map((item) => item.value)
        setRunningAssistant({ ...runningAssistant(), assistant_id, thread_id, files })
      } catch (err) {
        console.log(err)
      }
  }

  setInterval(async () => await UpdateStatus(), 2000)

  const CreateAssistant = async () => {
    if (processing()) return
    if (runningAssistant().assistant_id !== '') {
      alert('An AI Assistant is already running. Please delete it before creating a new one.')
      return
    }
    // if (settings().user === '' || settings().name === '' || settings().instructions === '' || settings().ciFiles === '') {
    //   alert('User ID, Assistant Name, Instructions and files are required to create an AI Assistant.')
    //   return
    // }
    if (settings().user === '' || settings().name === '' || settings().instructions === '') {
      alert('User ID, Assistant Name, and Instructions are required to create an AI Assistant.')
      return
    }

    setProcessing(true)
    const payload: IAssistantCreateRequest = {
      userName: settings().user,
      name: settings().name,
      instructions: settings().instructions,
      ci: settings().ci,
      ciFileURLs: settings().ciFileURLs.split(',').map((file) => file.trim()),
      fs: settings().fs,
      vs_name: settings().vs_name,
      fsFileURLs: settings().fsFileURLs.split(',').map((file) => file.trim()),
    }
    //alert(JSON.stringify(payload))
    try {
      const response = await axios.post<IAssistantCreateResponse>(POST_CREATE, payload)
      const data = response.data
      console.info(data)
      //alert(JSON.stringify(data))
      setRunningAssistant({ ...runningAssistant(), assistant_id: data.assistant_id, thread_id: data.thread_id, files: data.file_ids })
      // const obj: IRunningAssistant = { assistant_id: data.assistant_id, thread_id: data.thread_id, files: data.file_ids }
      // setRunningAssistant(obj)
    }
    catch (err) {
      console.log(err)
    }
    finally {
      setProcessing(false)
      await UpdateStatus()
    }
  }

  const Process = async () => {
    if (processing()) return
    try {
      let user_message = [{ role: 'user', content: prompt(), imageContent: '' }]
      setThreadMessages([...threadMessages(), ...user_message])
      const payload: { userName: string, prompt: string } = {
        userName: settings().user,
        prompt: prompt()
      }
      setProcessing(true)
      const response = await axios.post<IResponseMessage[]>(POST_PROCESS, payload)
      const additional_messages = response.data
      setThreadMessages([...threadMessages(), ...additional_messages])
      //console.log(JSON.stringify(threadMessages()))
      setPrompt('')
      setProcessing(false)
    }
    catch (err) {
      console.log(err)
    }
    finally {
      setProcessing(false)
    }
  }

  const DeleteAssistant = async () => {
    Swal.fire({
      title: 'Do you want delete the assistant?',
      showDenyButton: true,
      showCancelButton: true,
      confirmButtonText: 'Yes',
      denyButtonText: 'No',
      customClass: {
        actions: 'my-actions',
        cancelButton: 'order-1 right-gap',
        confirmButton: 'order-2',
        denyButton: 'order-3',
      },
    }).then(async (result) => {
      try {
        if (result.isConfirmed) {
          setProcessing(true)
          const response = await axios.delete(DELETE_ASSISTANT.replace('{name}', settings().user))
          console.log(response)
          setPrompt('')
          setSettings({ ...settings(), user: '', name: '', instructions: '', files: '' })
          setThreadMessages([])
          setRunningAssistant({ ...runningAssistant(), assistant_id: '', thread_id: '', files: [] })
        }
      }
      catch (err) {
        console.log(err)
      }
      setProcessing(false)
    })

  }

  const LoadSampleData = (scenario: string) => {
    let sampleSettings: ISettings = {
      user: '',
      name: 'Personal Assistant',
      instructions: 'You are an Assistant that can help analyze and perform calculations using the provided files. Use only the  data in this file Be polite, friendly, and helpful. After answering a user\'s question, say, "Can I be of further assistance."',
      ci: false,
      ciFileURLs: '',
      fs: false,
      fsFileURLs: '',
      vs_name: '',
    }
    switch (scenario) {
      case 'energy':
        sampleSettings.ciFileURLs = 'https://alemoraoaist.z13.web.core.windows.net/docs/Energy/wind_turbines_telemetry.csv'
        setPrompt('Chart the number of turbines by sector.')
        break
      case 'finance':
        sampleSettings.ciFileURLs = 'https://alemoraoaist.z13.web.core.windows.net/docs/finance/portfolio.csv'
        setPrompt('Chart the realized gain or loss for each of my investments.')
        break
      case 'faq':
        sampleSettings.ci = false
        sampleSettings.fs = true
        sampleSettings.vs_name = 'faq vector db'
        sampleSettings.fsFileURLs = 'https://stpdfdocsalemoreus.z13.web.core.windows.net/docs/contoso_faq.txt'
        setPrompt('What is the return policy?')
        sampleSettings.ciFileURLs = ''
        break
      case 'banking':
        sampleSettings.ci = true
        sampleSettings.ciFileURLs = 'https://stpdfdocsalemoreus.z13.web.core.windows.net/docs/banklist.csv'
        setPrompt('Chart the number of failed banks by State in the past 5 years.')
        sampleSettings.fs = false
        sampleSettings.fsFileURLs = ''
        break
      default:
        sampleSettings.ciFileURLs = 'https://alemoraoaist.z13.web.core.windows.net/docs/Energy/wind_turbines_telemetry.csv'
        setPrompt('Chart the number of turbines by sector.')
        break
    }
    setSettings(sampleSettings)
  }

  const StatusBarColor = () => {
    if (processing())
      return 'bg-red-600'

    if (runningAssistant().assistant_id === '')
      return 'bg-slate-500'
    else
      return 'bg-slate-900'
  }

  const forceDelete = async () => {
    try {
      await axios.delete(FORCE_DELETE_ASSISTANT)
    } catch (err) {
      console.log(err)
    }
  }

  return (
    <>
      <header class="bg-slate-950 text-white p-3 text-2xl font-bold h-[60px]">Assistants API Commander</header>
      <div class="flex flex-row h-[calc(100vh-100px)]">
        <aside class="bg-slate-200 p-2 w-1/4 overflow-auto">
          <div class="flex flex-col p-3 space-y-2">
            <label class="uppercase font-bold border-b-2 border-slate-800 text-lg">Assistant Settings</label>
            <label class="uppercase font-semibold">Email Address:</label>
            <input class='p-1 outline-none' type="email"
              onchange={(e) => setSettings({ ...settings(), user: e.target.value })}
              value={settings().user}
            />
            <label class="uppercase font-semibold">Assistant Name:</label>
            <input class='p-1 outline-none' type="text"
              onchange={(e) => setSettings({ ...settings(), name: e.target.value })}
              value={settings().name}
            />
            <label class="uppercase font-semibold">Instructions:</label>
            <textarea class='p-1 outline-none resize-none'
              rows={4}
              onchange={(e) => setSettings({ ...settings(), instructions: e.target.value })}
              value={settings().instructions}
            />
            <div class='flex'>
              <label class="uppercase font-semibold">Code Interpreter File URLs: <span><IoInformationCircleOutline class='inline-block' title='You can provide a comma separated list of files.' /></span></label>
            </div>
            <div class='flex space-x-1 text-sm'>
              <button class={'text-white p-1 ' + (settings().ci ? "bg-green-600" : "bg-slate-600")}
                onClick={() => setSettings({ ...settings(), ci: true })}
              >On</button>
              <button class={'text-white p-1 ' + (!settings().ci ? "bg-green-600" : "bg-slate-600")}
                onclick={() => setSettings({ ...settings(), ci: false })}
              >Off</button>
            </div>
            <textarea
              class='p-1 outline-none resize-none'
              rows={4}
              onchange={(e) => setSettings({ ...settings(), ciFileURLs: e.target.value })}
              value={settings().ciFileURLs}
            />
            <div class='space-x-1 text-sm font-semibold'>
              <span>Samples:</span>
              <button class="text-blue-600 hover:underline hover:font-semibold"
                onclick={() => LoadSampleData('banking')}
                disabled={runningAssistant().assistant_id !== ''}
              >Banking</button>
            </div>
            <div class='flex'><label class="uppercase font-semibold">File Search File URLs: <span><IoInformationCircleOutline class='inline-block' title='You can provide a comma separated list of files.' /></span></label></div>
            <div class='flex space-x-1 text-sm'>
              <button class={'text-white p-1 ' + (settings().fs ? "bg-green-600" : "bg-slate-600")}
                onClick={() => setSettings({ ...settings(), fs: true })}
              >On</button>
              <button class={'text-white p-1 ' + (!settings().fs ? "bg-green-600" : "bg-slate-600")}
                onclick={() => setSettings({ ...settings(), fs: false })}
              >Off</button>
            </div>
            <textarea
              class='p-1 outline-none resize-none'
              rows={4}
              onchange={(e) => setSettings({ ...settings(), fsFileURLs: e.target.value })}
              value={settings().fsFileURLs}
            />
          </div>
          <div class='px-3 space-x-1 text-sm font-semibold'>
            <span>Sample:</span>
            <button class="text-blue-600 hover:underline hover:font-semibold"
              onclick={() => LoadSampleData('faq')}
              disabled={runningAssistant().assistant_id !== ''}
            >FAQ</button>
          </div>
          <div class="flex flex-row space-x-2 p-3">
            <button class='w-20 p-2 bg-blue-600 text-white font-semibold disabled:bg-slate-500'
              onclick={CreateAssistant}
              disabled={runningAssistant().assistant_id !== ''}
            >Create</button>
            <button class='w-20 p-2 bg-blue-600 text-white font-semibold disabled:bg-slate-500'
              onclick={DeleteAssistant}
              disabled={runningAssistant().assistant_id === ''}
            >Delete</button>
            {/* <button class='w-20 p-2 bg-blue-700 text-white font-semibold disabled:bg-slate-500'
              onclick={LoadSampleData}
              disabled={runningAssistant().assistant_id !== ''}
            >Sample</button> */}
          </div>
          <div class="flex flex-col p-3 space-y-2">
            <label class="uppercase font-bold border-b-2 border-slate-800 text-lg">Available Tools</label>
            <span class='bg-slate-700 text-white rounded-xl p-1 w-24'>Stock Prices</span>
            <span class='bg-slate-700 text-white rounded-xl p-1 w-24'>Email</span>
            {/*<label class="uppercase font-bold border-b-2 border-slate-800 text-lg">Uploaded Files</label>
            <For each={runningAssistant().files}>
              {(file) => (
                <div class='flex flex-col bg-slate-400 rounded p-1 space-y-2'>
                  <label><strong>ID:</strong> {JSON.parse(file).id}</label>
                  <label><strong>FILE:</strong> {JSON.parse(file).name}</label>
                </div>
              )}
            </For>*/}
          </div>
        </aside >
        <main class="p-3 w-3/4 flex flex-col overflow-auto">
          <div class="flex flex-col">
            <div class="flex flex-row rounded-lg overflow-clip">
              <textarea class='outline-none p-2 w-full bg-blue-100'
                onchange={(e) => setPrompt(e.target.value)}
                value={prompt()}
                onkeydown={(e) => { if (e.key === 'Enter' && e.ctrlKey) Process() }}
                rows={5}></textarea>
              <button class='px-3 bg-blue-400 hover:bg-blue-700 font-semibold text-white'
                onclick={Process}
              ><IoSend /></button>
            </div>
            <div class='flex flex-col w-full space-y-2 mt-4'>
              <For each={threadMessages()}>
                {(message) => (<>
                  <div class={'w-[90%] p-1 rounded ' + (message.role !== "user" ? "bg-blue-300" : "bg-blue-400 ml-auto")}>
                    <SolidMarkdown children={message.content} />
                  </div>
                  <img class='w-[90%]' src={message.imageContent} alt="" />
                </>)}
              </For>
            </div>
          </div >
        </main >
      </div >
      <section class={"flex flex-wrap text-sm space-x-2 items-center h-[40px] text-white " + StatusBarColor()}>
        <span class={"bg-green-700 p-2 text-white uppercase " + (runningAssistant().assistant_id ? "visible" : "hidden")}>Assistant Loaded</span>
        <div class='space-x-2 p-2'><label class='uppercase font-semibold'>Assistant ID:</label><span class='p-1 bg-slate-800 text-white'>{runningAssistant().assistant_id}</span></div>
        <div class='space-x-2 p-2'><label class='uppercase font-semibold'>Thread ID:</label><span class='p-1 bg-slate-800 text-white'>{runningAssistant().thread_id}</span></div>
        <div class='space-x-2 p-2'><label class='uppercase font-semibold'>Files Loaded:</label><span class='p-1 bg-slate-800 text-white'>{runningAssistant().files.length}</span></div>
        <button class='bg-orange-600 text-white p-1 rounded'
          onClick={() => { setThreadMessages([]); setPrompt('') }}
        >Clear</button>
        <button class='bg-red-600 text-white p-1 rounded'
          onClick={() => { setSettings(Settings); setThreadMessages([]); setPrompt('') }}
        >Reset</button>
        <button class='bg-red-700 text-white p-1 rounded'
          onClick={() => { forceDelete(); setSettings(Settings); setThreadMessages([]); setPrompt('') }}
        >Force Delete</button>
        <span class={(processing() ? "visible" : "hidden")}><Spinner type={SpinnerType.puff} color="white" height={25} /></span>
      </section >
    </>
  )
}

export default App
